"""Explicit, sanitized real-provider smoke for structured Gateway services."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from .gateway.errors import GatewayError
from .gateway.intelligence import GatewayIntelligenceService
from .providers import ProviderConfig, resolve_provider

CONTRACT = "agent-gateway-v1"
_PROVIDER_KEY_NAMES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("minimax", ("MINIMAX_API_KEY",)),
    ("openai", ("OPENAI_API_KEY",)),
    ("deepseek", ("DEEPSEEK_API_KEY",)),
    ("kimi", ("MOONSHOT_API_KEY", "KIMI_API_KEY")),
)


class SmokeService(Protocol):
    async def translate(self, **kwargs: Any) -> dict[str, Any]: ...

    async def interpret_wish(self, **kwargs: Any) -> dict[str, Any]: ...


ServiceFactory = Callable[[ProviderConfig], SmokeService]


def _default_service_factory(config: ProviderConfig) -> GatewayIntelligenceService:
    return GatewayIntelligenceService(provider_resolver=lambda: config)


def _selected_provider(env: Mapping[str, str]) -> str:
    explicit = env.get("REAL_PROVIDER_E2E_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    configured = env.get("LLM_PROVIDER", "").strip().lower()
    if configured:
        return configured
    for provider, key_names in _PROVIDER_KEY_NAMES:
        if any(env.get(key_name, "").strip() for key_name in key_names):
            return provider
    return "minimax"


def _base_report(config: ProviderConfig) -> dict[str, Any]:
    return {
        "provider": config.provider,
        "model": config.model,
        "contract": CONTRACT,
    }


def _validate_provenance(result: dict[str, Any], config: ProviderConfig) -> None:
    provenance = result.get("provenance")
    if not isinstance(provenance, dict) or provenance != {
        "provider": config.provider,
        "model": config.model,
    }:
        raise ValueError("staging provenance contract mismatch")
    if not isinstance(result.get("warnings"), list):
        raise ValueError("staging warnings contract mismatch")


def _validate_translation(result: dict[str, Any], config: ProviderConfig) -> None:
    if set(result) != {"translated", "provenance", "warnings"}:
        raise ValueError("staging translation shape mismatch")
    translated = result["translated"]
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError("staging translation is empty")
    _validate_provenance(result, config)


def _validate_wish(
    result: dict[str, Any],
    config: ProviderConfig,
    *,
    expected_phase: str,
) -> None:
    if set(result) != {"reply", "wish", "provenance", "warnings"}:
        raise ValueError("staging wish shape mismatch")
    wish = result.get("wish")
    if not isinstance(wish, dict) or wish.get("phase") != expected_phase:
        raise ValueError("staging wish phase mismatch")
    if expected_phase == "confirming" and set(wish) != {
        "phase",
        "title",
        "type",
        "priority",
        "requirements",
        "summary",
    }:
        raise ValueError("staging confirming wish is incomplete")
    _validate_provenance(result, config)


async def run_staging_smoke(
    *,
    env: Mapping[str, str] | None = None,
    service_factory: ServiceFactory = _default_service_factory,
    monotonic: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """Run three bounded calls only when both the explicit flag and provider key exist."""

    values = os.environ if env is None else env
    if values.get("RUN_REAL_PROVIDER_E2E") != "1":
        return {
            "status": "skipped",
            "contract": CONTRACT,
            "reason": "opt_in_disabled",
        }

    provider = _selected_provider(values)
    try:
        config = resolve_provider(provider, env=values)
    except ValueError:
        return {
            "status": "failed",
            "provider": provider,
            "contract": CONTRACT,
            "error": {
                "code": "PROVIDER_CONFIG_ERROR",
                "status_code": 503,
                "retryable": False,
            },
        }
    if not config.api_key:
        return {
            "status": "skipped",
            **_base_report(config),
            "reason": "provider_key_missing",
        }

    service = service_factory(config)
    checks: list[dict[str, Any]] = []
    try:
        started = monotonic()
        translation = await service.translate(
            text="ソフトバンク株が上昇",
            source_language="ja",
            target_language="zh-CN",
        )
        latency_ms = round((monotonic() - started) * 1000)
        _validate_translation(translation, config)
        checks.append(
            {
                "name": "translation",
                "latency_ms": latency_ms,
                "contract_valid": True,
            }
        )

        started = monotonic()
        clarifying = await service.interpret_wish(
            message="我有一个产品愿望，但暂时没有提供具体内容，请询问需要补充的信息。",
            history=[],
        )
        latency_ms = round((monotonic() - started) * 1000)
        _validate_wish(clarifying, config, expected_phase="clarifying")
        checks.append(
            {
                "name": "wish_clarifying",
                "latency_ms": latency_ms,
                "contract_valid": True,
                "phase": "clarifying",
            }
        )

        started = monotonic()
        confirming = await service.interpret_wish(
            message=(
                "类型是feature，优先级medium，要求支持1m、5m和15m周期切换。"
                "请整理完整需求并进入待确认阶段，不要标记为已确认。"
            ),
            history=[
                {
                    "role": "user",
                    "content": "我希望行情页增加多周期K线切换。",
                }
            ],
        )
        latency_ms = round((monotonic() - started) * 1000)
        _validate_wish(confirming, config, expected_phase="confirming")
        checks.append(
            {
                "name": "wish_confirming",
                "latency_ms": latency_ms,
                "contract_valid": True,
                "phase": "confirming",
            }
        )
    except GatewayError as exc:
        return {
            "status": "failed",
            **_base_report(config),
            "error": {
                "code": exc.code,
                "status_code": exc.status_code,
                "retryable": exc.retryable,
            },
        }
    except Exception as exc:
        return {
            "status": "failed",
            **_base_report(config),
            "error": {
                "code": "SMOKE_CONTRACT_ERROR",
                "exception": type(exc).__name__,
                "retryable": False,
            },
        }

    return {
        "status": "passed",
        **_base_report(config),
        "checks": checks,
    }


def safe_report_json(report: Mapping[str, Any]) -> str:
    """Serialize only the runner's allowlisted summary, never service output."""

    safe: dict[str, Any] = {
        key: report[key]
        for key in ("status", "provider", "model", "contract", "reason")
        if key in report
    }
    checks = report.get("checks")
    if isinstance(checks, list):
        safe["checks"] = [
            {
                key: check[key]
                for key in ("name", "latency_ms", "contract_valid", "phase")
                if isinstance(check, Mapping) and key in check
            }
            for check in checks
            if isinstance(check, Mapping)
        ]
    error = report.get("error")
    if isinstance(error, Mapping):
        safe["error"] = {
            key: error[key]
            for key in ("code", "status_code", "retryable", "exception")
            if key in error
        }
    return json.dumps(safe, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def main() -> None:
    report = asyncio.run(run_staging_smoke())
    print(safe_report_json(report))
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
