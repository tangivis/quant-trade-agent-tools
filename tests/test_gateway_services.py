from __future__ import annotations

from typing import Any

import httpx
import pytest

from agent_tools.gateway.context import ContextSnapshot
from agent_tools.gateway.errors import GatewayError
from agent_tools.gateway.services import GatewayChatService, LegacyAnalysisProvider
from agent_tools.providers import ProviderConfig


def complete_snapshot() -> ContextSnapshot:
    return ContextSnapshot(
        symbol="9984.T",
        as_of="2026-09-01T00:00:00+00:00",
        facts={"quote": {"price": 15500}},
        sources={"quote": {"ok": True}},
        warnings=["delayed_market_data"],
        derived={
            "current_price": 15500.0,
            "regime": "WeakUp",
            "adx": 25.0,
            "rsi": 57.5,
            "news_sentiment": 0.2,
            "tweet_sentiment": 0.1,
            "tweet_count": 2,
        },
    )


class AnalyzeClient:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None
        self.closed = False

    def legacy_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payload = payload
        return {
            "signal": "BUY",
            "confidence": 0.7,
            "reason": "趋势与情感一致",
            "final_action": "BUY",
            "approved": True,
            "risk_notes": "控制仓位",
            "trend_direction": "up",
            "news_summary": "偏正面",
        }

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_legacy_provider_maps_snapshot_and_normalizes_response() -> None:
    client = AnalyzeClient()
    provider = LegacyAnalysisProvider(client_factory=lambda: client)

    result = await provider.analyze(complete_snapshot(), "当前风险？")

    assert client.payload == {
        "symbol": "9984.T",
        "current_price": 15500.0,
        "regime": "WeakUp",
        "rsi": 57.5,
        "adx": 25.0,
        "news_sentiment": 0.2,
        "tweet_sentiment": 0.1,
        "tweet_count": 2,
    }
    assert result["decision"] == {
        "action": "BUY",
        "confidence": 0.7,
        "approved": True,
        "risk_notes": ["控制仓位"],
    }
    assert result["analysis"]["question"] == "当前风险？"
    assert result["provenance"]["provider"] == "legacy"
    assert client.closed is True


class RegistryClient:
    def close(self) -> None:
        pass


class FakeAgent:
    def __init__(self, tool_names: list[str]) -> None:
        self.tool_names = tool_names

    def run(
        self,
        prompt: str,
        *,
        history: list[dict[str, str]] | None = None,
        context_summary: str | None = None,
        selected_symbol: str | None = None,
    ) -> str:
        if context_summary:
            return f"{prompt}:{len(history or [])}:{context_summary}"
        return f"{prompt}:{len(history or [])}"

    def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_chat_service_blocks_benchmark_by_default() -> None:
    seen_tools: list[list[str]] = []

    def agent_factory(*, config, tools):
        seen_tools.append(tools.names())
        return FakeAgent(tools.names())

    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=agent_factory,
    )

    result = await service.run(
        message="分析",
        history=[{"role": "user", "content": "历史"}],
        context_summary=None,
        symbol="9984.T",
        allow_expensive_tools=False,
    )

    assert "benchmark" not in seen_tools[0]
    assert "conversation_create" not in seen_tools[0]
    assert "conversation_context" not in seen_tools[0]
    assert "conversation_append" not in seen_tools[0]
    assert result["answer"] == "分析:1"


@pytest.mark.asyncio
async def test_chat_service_allows_benchmark_only_when_explicit() -> None:
    seen_tools: list[list[str]] = []

    def agent_factory(*, config, tools):
        seen_tools.append(tools.names())
        return FakeAgent(tools.names())

    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=agent_factory,
    )

    await service.run(
        message="扫描参数",
        history=[],
        context_summary=None,
        symbol="9984.T",
        allow_expensive_tools=True,
    )

    assert "benchmark" in seen_tools[0]
    assert "conversation_create" not in seen_tools[0]
    assert "conversation_context" not in seen_tools[0]
    assert "conversation_append" not in seen_tools[0]


@pytest.mark.asyncio
async def test_chat_service_normalizes_agent_runtime_failure() -> None:
    class FailingAgent(FakeAgent):
        def run(
            self,
            prompt: str,
            *,
            history: list[dict[str, str]] | None = None,
            context_summary: str | None = None,
            selected_symbol: str | None = None,
        ) -> str:
            raise RuntimeError("iteration limit reached")

    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=lambda **kwargs: FailingAgent(kwargs["tools"].names()),
    )

    with pytest.raises(GatewayError) as captured:
        await service.run(
            message="分析",
            history=[],
            context_summary=None,
            symbol="9984.T",
            allow_expensive_tools=False,
        )

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert "iteration limit reached" not in captured.value.message


@pytest.mark.asyncio
async def test_chat_service_marks_provider_rate_limit_retryable() -> None:
    class RateLimitedAgent(FakeAgent):
        def run(
            self,
            prompt: str,
            *,
            history: list[dict[str, str]] | None = None,
            context_summary: str | None = None,
            selected_symbol: str | None = None,
        ) -> str:
            request = httpx.Request("POST", "http://model.test/v1/chat/completions")
            response = httpx.Response(429, request=request)
            raise httpx.HTTPStatusError(
                "rate limited",
                request=request,
                response=response,
            )

    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=lambda **kwargs: RateLimitedAgent(kwargs["tools"].names()),
    )

    with pytest.raises(GatewayError) as captured:
        await service.run(
            message="分析",
            history=[],
            context_summary=None,
            symbol="9984.T",
            allow_expensive_tools=False,
        )

    assert captured.value.code == "MODEL_RATE_LIMIT"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_chat_service_supports_murata_and_context_summary() -> None:
    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=lambda **kwargs: FakeAgent(kwargs["tools"].names()),
    )

    result = await service.run(
        message="继续",
        history=[],
        context_summary="用户关注村田制作所。",
        symbol="6981.T",
        allow_expensive_tools=False,
    )

    assert result["answer"] == "继续:0:用户关注村田制作所。"


@pytest.mark.asyncio
async def test_chat_service_passes_the_validated_symbol_to_the_agent() -> None:
    selected_symbols: list[str | None] = []

    class CapturingAgent(FakeAgent):
        def run(
            self,
            prompt: str,
            *,
            history: list[dict[str, str]] | None = None,
            context_summary: str | None = None,
            selected_symbol: str | None = None,
        ) -> str:
            selected_symbols.append(selected_symbol)
            return "完成"

    service = GatewayChatService(
        client_factory=RegistryClient,
        provider_resolver=lambda: ProviderConfig(
            provider="fake", base_url="http://model.test/v1", model="fake", api_key=""
        ),
        agent_factory=lambda **kwargs: CapturingAgent(kwargs["tools"].names()),
    )

    await service.run(
        message="分析村田",
        history=[],
        context_summary=None,
        symbol="6981.T",
        allow_expensive_tools=False,
    )

    assert selected_symbols == ["6981.T"]
