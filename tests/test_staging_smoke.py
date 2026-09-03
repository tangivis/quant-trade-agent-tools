from __future__ import annotations

import inspect
import json
import os
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from agent_tools import staging_smoke
from agent_tools.gateway.errors import GatewayError
from agent_tools.providers import ProviderConfig


class ExplodingFactory:
    def __init__(self) -> None:
        self.called = False

    def __call__(self, _config: ProviderConfig) -> Any:
        self.called = True
        raise AssertionError("network-capable service must not be constructed")


class FakeService:
    def __init__(self, *, fail: GatewayError | None = None) -> None:
        self.fail = fail
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def translate(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("translation", kwargs))
        if self.fail is not None:
            raise self.fail
        return {
            "translated": "模型原始敏感译文CANARY_TRANSLATION",
            "provenance": {"provider": "minimax", "model": "MiniMax-M3"},
            "warnings": [],
        }

    async def interpret_wish(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("wish", kwargs))
        if len([name for name, _payload in self.calls if name == "wish"]) == 1:
            return {
                "reply": "模型原始敏感澄清CANARY_CLARIFYING",
                "wish": {"phase": "clarifying"},
                "provenance": {"provider": "minimax", "model": "MiniMax-M3"},
                "warnings": [],
            }
        return {
            "reply": "模型原始敏感确认CANARY_CONFIRMING",
            "wish": {
                "phase": "confirming",
                "title": "行情页多周期K线",
                "type": "feature",
                "priority": "medium",
                "requirements": ["支持1m、5m和15m周期切换"],
                "summary": "行情页支持多周期K线切换",
            },
            "provenance": {"provider": "minimax", "model": "MiniMax-M3"},
            "warnings": [],
        }


def clock(values: list[float]) -> Callable[[], float]:
    iterator: Iterator[float] = iter(values)
    return lambda: next(iterator)


@pytest.mark.asyncio
async def test_staging_smoke_is_network_disabled_by_default() -> None:
    factory = ExplodingFactory()

    report = await staging_smoke.run_staging_smoke(
        env={"MINIMAX_API_KEY": "CANARY_KEY"},
        service_factory=factory,
    )

    assert report == {
        "status": "skipped",
        "contract": "agent-gateway-v1",
        "reason": "opt_in_disabled",
    }
    assert factory.called is False


@pytest.mark.asyncio
async def test_staging_smoke_skips_before_service_construction_without_key() -> None:
    factory = ExplodingFactory()

    report = await staging_smoke.run_staging_smoke(
        env={
            "RUN_REAL_PROVIDER_E2E": "1",
            "REAL_PROVIDER_E2E_PROVIDER": "minimax",
        },
        service_factory=factory,
    )

    assert report["status"] == "skipped"
    assert report["reason"] == "provider_key_missing"
    assert report["provider"] == "minimax"
    assert report["model"] == "MiniMax-M3"
    assert factory.called is False


@pytest.mark.asyncio
async def test_staging_smoke_runs_three_contract_checks_and_redacts_results() -> None:
    service = FakeService()
    seen_config: list[ProviderConfig] = []

    def factory(config: ProviderConfig) -> FakeService:
        seen_config.append(config)
        return service

    report = await staging_smoke.run_staging_smoke(
        env={
            "RUN_REAL_PROVIDER_E2E": "1",
            "REAL_PROVIDER_E2E_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "CANARY_KEY",
        },
        service_factory=factory,
        monotonic=clock([0.0, 1.25, 2.0, 4.5, 5.0, 8.75]),
    )

    assert report == {
        "status": "passed",
        "provider": "minimax",
        "model": "MiniMax-M3",
        "contract": "agent-gateway-v1",
        "checks": [
            {
                "name": "translation",
                "latency_ms": 1250,
                "contract_valid": True,
            },
            {
                "name": "wish_clarifying",
                "latency_ms": 2500,
                "contract_valid": True,
                "phase": "clarifying",
            },
            {
                "name": "wish_confirming",
                "latency_ms": 3750,
                "contract_valid": True,
                "phase": "confirming",
            },
        ],
    }
    assert seen_config[0].api_key == "CANARY_KEY"
    assert [name for name, _payload in service.calls] == [
        "translation",
        "wish",
        "wish",
    ]
    assert service.calls[1][1]["history"] == []
    assert service.calls[2][1]["history"][0]["role"] == "user"

    serialized = staging_smoke.safe_report_json(report)
    for canary in (
        "CANARY_KEY",
        "CANARY_TRANSLATION",
        "CANARY_CLARIFYING",
        "CANARY_CONFIRMING",
        "ソフトバンク",
        "行情页",
    ):
        assert canary not in serialized


@pytest.mark.asyncio
async def test_staging_smoke_failure_report_does_not_include_exception_message() -> None:
    failure = GatewayError(
        code="MODEL_ERROR",
        message="CANARY_KEY provider body CANARY_PROMPT",
        status_code=502,
        retryable=True,
    )

    report = await staging_smoke.run_staging_smoke(
        env={
            "RUN_REAL_PROVIDER_E2E": "1",
            "REAL_PROVIDER_E2E_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "CANARY_KEY",
        },
        service_factory=lambda _config: FakeService(fail=failure),
    )

    assert report["status"] == "failed"
    assert report["error"] == {
        "code": "MODEL_ERROR",
        "status_code": 502,
        "retryable": True,
    }
    serialized = staging_smoke.safe_report_json(report)
    assert "CANARY_KEY" not in serialized
    assert "CANARY_PROMPT" not in serialized
    assert "provider body" not in serialized


def test_staging_smoke_source_has_no_gitlab_product_or_trading_mutation() -> None:
    source = inspect.getsource(staging_smoke)

    for forbidden in (
        "GITLAB_TOKEN",
        "PRIVATE-TOKEN",
        "create_issue",
        "/api/wish",
        "place_order",
        "cancel_order",
        "psycopg",
        "sqlalchemy",
    ):
        assert forbidden not in source


def test_safe_report_json_has_a_stable_compact_shape() -> None:
    rendered = staging_smoke.safe_report_json(
        {
            "status": "skipped",
            "contract": "agent-gateway-v1",
            "reason": "opt_in_disabled",
        }
    )

    assert json.loads(rendered)["status"] == "skipped"
    assert "\n" not in rendered


def test_safe_report_json_drops_unknown_sensitive_fields() -> None:
    rendered = staging_smoke.safe_report_json(
        {
            "status": "passed",
            "provider": "minimax",
            "model": "MiniMax-M3",
            "contract": "agent-gateway-v1",
            "raw_prompt": "CANARY_PROMPT",
            "api_key": "CANARY_KEY",
            "checks": [
                {
                    "name": "translation",
                    "latency_ms": 10,
                    "contract_valid": True,
                    "raw_output": "CANARY_OUTPUT",
                }
            ],
        }
    )

    assert json.loads(rendered) == {
        "checks": [
            {
                "contract_valid": True,
                "latency_ms": 10,
                "name": "translation",
            }
        ],
        "contract": "agent-gateway-v1",
        "model": "MiniMax-M3",
        "provider": "minimax",
        "status": "passed",
    }
    assert "CANARY" not in rendered


@pytest.mark.asyncio
async def test_real_provider_staging_smoke() -> None:
    if os.environ.get("RUN_REAL_PROVIDER_E2E") != "1":
        pytest.skip("real provider smoke is opt-in")

    report = await staging_smoke.run_staging_smoke()
    if report["status"] == "skipped":
        pytest.skip(str(report["reason"]))

    print(staging_smoke.safe_report_json(report))
    assert report["status"] == "passed", staging_smoke.safe_report_json(report)
