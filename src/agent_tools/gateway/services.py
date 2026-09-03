"""Gateway orchestration services for native/legacy analysis and native chat."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable
from typing import Any, Protocol

import httpx

from ..agent import OpenAICompatibleAgent
from ..client import QuantTradeClient
from ..providers import ProviderConfig, resolve_provider
from ..tools import ToolRegistry, build_tool_registry
from .context import ContextSnapshot
from .errors import GatewayError
from .intelligence import (
    StructuredModelExecutor,
    StructuredOutputClient,
    model_response_error,
)

_ANALYSIS_ACTIONS = {"BUY", "HOLD", "SELL"}
_TREND_DIRECTIONS = {"UP", "DOWN", "SIDEWAYS", "UNCLEAR"}


class AnalysisProvider(Protocol):
    async def analyze(
        self,
        snapshot: ContextSnapshot,
        question: str | None,
    ) -> dict[str, Any]: ...


class NativeAnalysisProvider:
    """Produce layered decision support from server-owned facts and one LLM call."""

    def __init__(
        self,
        *,
        provider_resolver: Callable[[], ProviderConfig] = resolve_provider,
        structured_client: StructuredOutputClient | None = None,
    ) -> None:
        self.model_executor = StructuredModelExecutor(
            provider_resolver=provider_resolver,
            structured_client=structured_client,
        )

    async def analyze(
        self,
        snapshot: ContextSnapshot,
        question: str | None,
    ) -> dict[str, Any]:
        required = ("current_price", "regime", "rsi", "adx", "news_sentiment")
        missing = [name for name in required if snapshot.derived.get(name) is None]
        if not snapshot.facts:
            missing.insert(0, "facts")
        if missing:
            raise GatewayError(
                code="CONTEXT_INCOMPLETE",
                message=f"required analysis context is missing: {', '.join(missing)}",
                status_code=503,
                retryable=True,
            )

        config = self.model_executor.resolve_config()
        structured = await self.model_executor.complete(
            config=config,
            task_name="record_native_analysis",
            task_description=(
                "Record a bounded market analysis and non-executable decision-support "
                "classification from the supplied server-owned facts."
            ),
            system_prompt=(
                "Use only the supplied server-owned facts. Return the required structured "
                "tool call. This is decision support only: never place, modify, cancel, or "
                "execute an order; approved is informational and never authorizes execution. "
                "Do not invent market facts."
            ),
            user_payload={
                "symbol": snapshot.symbol,
                "as_of": snapshot.as_of,
                "facts": snapshot.facts,
                "derived": snapshot.derived,
                "question": question,
            },
            output_schema=self._output_schema(),
            max_tokens=1200,
        )
        normalized = self._validate_output(structured)
        warnings = list(
            dict.fromkeys([*snapshot.warnings, "decision_support_only"])
        )
        return {
            "facts": snapshot.facts,
            "analysis": {
                "summary": normalized["summary"],
                "trend_direction": normalized["trend_direction"],
            },
            "decision": {
                "action": normalized["action"],
                "confidence": normalized["confidence"],
                "approved": normalized["approved"],
                "risk_notes": normalized["risk_notes"],
            },
            "provenance": {
                "provider": config.provider,
                "model": config.model,
                "tools": [
                    name
                    for name, metadata in snapshot.sources.items()
                    if metadata.get("ok") is True
                ],
            },
            "warnings": warnings,
        }

    @classmethod
    def _validate_output(cls, payload: dict[str, Any]) -> dict[str, Any]:
        expected = {
            "summary",
            "trend_direction",
            "action",
            "confidence",
            "approved",
            "risk_notes",
        }
        if not isinstance(payload, dict) or set(payload) != expected:
            raise model_response_error()

        summary = cls._text(payload["summary"], max_length=2000)
        trend_direction = payload["trend_direction"]
        if not isinstance(trend_direction, str) or trend_direction not in _TREND_DIRECTIONS:
            raise model_response_error()
        action = payload["action"]
        if not isinstance(action, str) or action not in _ANALYSIS_ACTIONS:
            raise model_response_error()
        raw_confidence = payload["confidence"]
        if isinstance(raw_confidence, bool) or not isinstance(
            raw_confidence, (int, float)
        ):
            raise model_response_error()
        confidence = float(raw_confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise model_response_error()
        approved = payload["approved"]
        if type(approved) is not bool:
            raise model_response_error()
        risk_notes = payload["risk_notes"]
        if not isinstance(risk_notes, list) or len(risk_notes) > 20:
            raise model_response_error()
        normalized_notes = [cls._text(note, max_length=500) for note in risk_notes]
        return {
            "summary": summary,
            "trend_direction": trend_direction,
            "action": action,
            "confidence": confidence,
            "approved": approved,
            "risk_notes": normalized_notes,
        }

    @staticmethod
    def _text(value: Any, *, max_length: int) -> str:
        if not isinstance(value, str):
            raise model_response_error()
        text = value.strip()
        if not text or len(text) > max_length:
            raise model_response_error()
        return text

    @staticmethod
    def _output_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "minLength": 1, "maxLength": 2000},
                "trend_direction": {
                    "type": "string",
                    "enum": sorted(_TREND_DIRECTIONS),
                },
                "action": {"type": "string", "enum": sorted(_ANALYSIS_ACTIONS)},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "approved": {"type": "boolean"},
                "risk_notes": {
                    "type": "array",
                    "maxItems": 20,
                    "items": {"type": "string", "minLength": 1, "maxLength": 500},
                },
            },
            "required": [
                "summary",
                "trend_direction",
                "action",
                "confidence",
                "approved",
                "risk_notes",
            ],
            "additionalProperties": False,
        }


class LegacyAnalysisProvider:
    def __init__(
        self,
        *,
        client_factory: Callable[[], QuantTradeClient] = QuantTradeClient,
    ) -> None:
        self.client_factory = client_factory

    async def analyze(
        self,
        snapshot: ContextSnapshot,
        question: str | None,
    ) -> dict[str, Any]:
        payload = {
            "symbol": snapshot.symbol,
            "current_price": snapshot.derived.get("current_price"),
            "regime": snapshot.derived.get("regime"),
            "rsi": snapshot.derived.get("rsi"),
            "adx": snapshot.derived.get("adx"),
            "news_sentiment": snapshot.derived.get("news_sentiment"),
            "tweet_sentiment": snapshot.derived.get("tweet_sentiment") or 0.0,
            "tweet_count": snapshot.derived.get("tweet_count") or 0,
        }
        missing = [
            name
            for name in ("current_price", "regime", "rsi", "adx", "news_sentiment")
            if payload[name] is None
        ]
        if missing:
            raise GatewayError(
                code="CONTEXT_INCOMPLETE",
                message=f"required analysis context is missing: {', '.join(missing)}",
                status_code=503,
                retryable=True,
            )

        client = self.client_factory()
        try:
            response = await asyncio.to_thread(client.analyze, payload)
        except httpx.TimeoutException as exc:
            raise GatewayError(
                code="UPSTREAM_TIMEOUT",
                message="分析服务超时",
                status_code=504,
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise GatewayError(
                    code="UPSTREAM_RATE_LIMIT",
                    message="分析服务请求过于频繁",
                    status_code=503,
                    retryable=True,
                ) from exc
            raise GatewayError(
                code="UPSTREAM_ERROR",
                message="分析服务返回异常",
                status_code=502,
                retryable=exc.response.status_code >= 500,
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise GatewayError(
                code="UPSTREAM_ERROR",
                message="分析服务返回异常",
                status_code=502,
                retryable=True,
            ) from exc
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

        action = response.get("final_action") or response.get("signal") or "HOLD"
        confidence = response.get("confidence", 0.0)
        approved = response.get("approved", False)
        risk_notes = response.get("risk_notes")
        if isinstance(risk_notes, str):
            normalized_risk_notes = [risk_notes]
        elif isinstance(risk_notes, list):
            normalized_risk_notes = [str(item) for item in risk_notes]
        else:
            normalized_risk_notes = []

        return {
            "facts": snapshot.facts,
            "analysis": {
                "summary": response.get("reason", ""),
                "question": question,
                "trend_direction": response.get("trend_direction"),
                "news_summary": response.get("news_summary"),
            },
            "decision": {
                "action": str(action),
                "confidence": float(confidence),
                "approved": bool(approved),
                "risk_notes": normalized_risk_notes,
            },
            "provenance": {
                "provider": "legacy",
                "model": "quant_trade/backend_llm",
                "tools": [
                    name
                    for name, metadata in snapshot.sources.items()
                    if metadata.get("ok") is True
                ],
            },
            "warnings": [*snapshot.warnings, "decision_support_only"],
        }


AgentFactory = Callable[..., OpenAICompatibleAgent]


class GatewayChatService:
    def __init__(
        self,
        *,
        client_factory: Callable[[], QuantTradeClient] = QuantTradeClient,
        provider_resolver: Callable[[], ProviderConfig] = resolve_provider,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self.client_factory = client_factory
        self.provider_resolver = provider_resolver
        self.agent_factory = agent_factory or self._create_agent

    @staticmethod
    def _create_agent(
        *,
        config: ProviderConfig,
        tools: ToolRegistry,
    ) -> OpenAICompatibleAgent:
        return OpenAICompatibleAgent(config=config, tools=tools)

    async def run(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        context_summary: str | None,
        symbol: str,
        allow_expensive_tools: bool,
    ) -> dict[str, Any]:
        if symbol not in {"9984.T", "6981.T"}:
            raise GatewayError(
                code="UNSUPPORTED_SYMBOL",
                message=f"不支持的标的: {symbol}",
                status_code=422,
            )
        try:
            config = self.provider_resolver()
        except ValueError as exc:
            raise GatewayError(
                code="PROVIDER_CONFIG_ERROR",
                message=str(exc),
                status_code=503,
            ) from exc

        client = self.client_factory()
        registry = build_tool_registry(client).without(
            {"conversation_create", "conversation_context", "conversation_append"}
        )
        if not allow_expensive_tools:
            registry = registry.without({"benchmark"})
        agent = self.agent_factory(config=config, tools=registry)
        try:
            answer = await asyncio.to_thread(
                agent.run,
                message,
                history=history,
                context_summary=context_summary,
            )
            used_tools = list(getattr(agent, "last_tool_names", []))
        except httpx.TimeoutException as exc:
            raise GatewayError(
                code="MODEL_TIMEOUT",
                message="模型服务超时",
                status_code=504,
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise GatewayError(
                    code="MODEL_RATE_LIMIT",
                    message="模型服务请求过于频繁",
                    status_code=503,
                    retryable=True,
                ) from exc
            raise GatewayError(
                code="MODEL_ERROR",
                message="模型服务返回异常",
                status_code=502,
                retryable=exc.response.status_code >= 500,
            ) from exc
        except httpx.HTTPError as exc:
            raise GatewayError(
                code="MODEL_ERROR",
                message="模型服务返回异常",
                status_code=502,
                retryable=True,
            ) from exc
        except (RuntimeError, ValueError) as exc:
            raise GatewayError(
                code="MODEL_RESPONSE_ERROR",
                message="模型响应无法完成或不符合契约",
                status_code=502,
            ) from exc
        finally:
            close_agent = getattr(agent, "close", None)
            if callable(close_agent):
                close_agent()
            close_client = getattr(client, "close", None)
            if callable(close_client):
                close_client()

        return {
            "answer": answer,
            "provider": config.provider,
            "model": config.model,
            "tools": used_tools,
        }
