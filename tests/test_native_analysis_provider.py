from __future__ import annotations

import math
from typing import Any

import httpx
import pytest

from agent_tools.gateway.context import ContextSnapshot
from agent_tools.gateway.errors import GatewayError
from agent_tools.gateway.services import NativeAnalysisProvider
from agent_tools.providers import ProviderConfig


CONFIG = ProviderConfig(
    provider="deepseek",
    base_url="http://model.test/v1",
    model="deepseek-chat",
    api_key="fake-key",
)


def complete_snapshot() -> ContextSnapshot:
    return ContextSnapshot(
        symbol="9984.T",
        as_of="2026-09-01T00:00:00+00:00",
        facts={
            "quote": {"price": 15500.0},
            "trending": {"regime": "StrongUp", "adx_value": 28.0},
            "signals": {"signals": [{"source": "MA_CROSS"}]},
        },
        sources={
            "quote": {"ok": True},
            "trending": {"ok": True},
            "signals": {"ok": True},
            "news": {"ok": False, "error": "TimeoutException"},
        },
        warnings=["delayed_market_data", "source_unavailable:news"],
        derived={
            "current_price": 15500.0,
            "regime": "StrongUp",
            "rsi": 58.0,
            "adx": 28.0,
            "news_sentiment": 0.25,
            "tweet_sentiment": None,
            "tweet_count": 0,
        },
    )


VALID_OUTPUT = {
    "summary": "趋势偏强，但波动率仍高",
    "trend_direction": "UP",
    "action": "HOLD",
    "confidence": 0.72,
    "approved": False,
    "risk_notes": ["波动率较高"],
}


class FakeStructuredClient:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if isinstance(self.response, BaseException):
            raise self.response
        assert isinstance(self.response, dict)
        return self.response


def build_provider(response: object = VALID_OUTPUT) -> tuple[NativeAnalysisProvider, FakeStructuredClient]:
    client = FakeStructuredClient(response)
    provider = NativeAnalysisProvider(
        provider_resolver=lambda: CONFIG,
        structured_client=client,
    )
    return provider, client


@pytest.mark.asyncio
async def test_native_analysis_returns_consumer_compatible_layered_response() -> None:
    provider, client = build_provider()
    snapshot = complete_snapshot()

    result = await provider.analyze(snapshot, "当前风险？")

    assert result == {
        "facts": snapshot.facts,
        "analysis": {
            "summary": "趋势偏强，但波动率仍高",
            "trend_direction": "UP",
        },
        "decision": {
            "action": "HOLD",
            "confidence": 0.72,
            "approved": False,
            "risk_notes": ["波动率较高"],
        },
        "provenance": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "tools": ["quote", "trending", "signals"],
        },
        "warnings": [
            "delayed_market_data",
            "source_unavailable:news",
            "decision_support_only",
        ],
    }
    assert len(client.calls) == 1
    assert client.calls[0]["task_name"] == "record_native_analysis"
    assert client.calls[0]["output_schema"]["additionalProperties"] is False
    assert client.calls[0]["output_schema"]["required"] == [
        "summary",
        "trend_direction",
        "action",
        "confidence",
        "approved",
        "risk_notes",
    ]
    assert client.calls[0]["user_payload"] == {
        "symbol": "9984.T",
        "as_of": "2026-09-01T00:00:00+00:00",
        "facts": snapshot.facts,
        "derived": snapshot.derived,
        "question": "当前风险？",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action", "confidence"),
    [("BUY", 0.0), ("HOLD", 0.5), ("SELL", 1.0)],
)
async def test_native_analysis_accepts_action_and_confidence_contract_boundaries(
    action: str,
    confidence: float,
) -> None:
    provider, _client = build_provider(
        {**VALID_OUTPUT, "action": action, "confidence": confidence}
    )

    result = await provider.analyze(complete_snapshot(), None)

    assert result["decision"]["action"] == action
    assert result["decision"]["confidence"] == confidence


@pytest.mark.asyncio
@pytest.mark.parametrize("empty_facts", [True, False])
async def test_native_analysis_rejects_empty_or_incomplete_context_without_model_call(
    empty_facts: bool,
) -> None:
    provider, client = build_provider()
    snapshot = complete_snapshot()
    snapshot = ContextSnapshot(
        symbol=snapshot.symbol,
        as_of=snapshot.as_of,
        facts={} if empty_facts else snapshot.facts,
        sources=snapshot.sources,
        warnings=snapshot.warnings,
        derived=(
            snapshot.derived
            if empty_facts
            else {key: value for key, value in snapshot.derived.items() if key != "rsi"}
        ),
    )

    with pytest.raises(GatewayError) as captured:
        await provider.analyze(snapshot, None)

    assert captured.value.code == "CONTEXT_INCOMPLETE"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True
    assert client.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_output",
    [
        {**VALID_OUTPUT, "action": "WAIT"},
        {**VALID_OUTPUT, "confidence": -0.01},
        {**VALID_OUTPUT, "confidence": 1.01},
        {**VALID_OUTPUT, "confidence": math.nan},
        {**VALID_OUTPUT, "summary": "  "},
        {**VALID_OUTPUT, "trend_direction": "STRONG_UP"},
        {**VALID_OUTPUT, "approved": 1},
        {**VALID_OUTPUT, "risk_notes": [""]},
        {**VALID_OUTPUT, "model_supplied_facts": {"price": 1}},
    ],
)
async def test_native_analysis_rejects_invalid_structured_output(
    invalid_output: dict[str, Any],
) -> None:
    provider, _client = build_provider(invalid_output)

    with pytest.raises(GatewayError) as captured:
        await provider.analyze(complete_snapshot(), None)

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert captured.value.status_code == 502
    assert captured.value.retryable is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "code", "status", "retryable"),
    [
        (httpx.TimeoutException("secret timeout"), "MODEL_TIMEOUT", 504, True),
        (httpx.ConnectError("secret down"), "MODEL_ERROR", 502, True),
    ],
)
async def test_native_analysis_normalizes_provider_transport_failures(
    failure: Exception,
    code: str,
    status: int,
    retryable: bool,
) -> None:
    provider, _client = build_provider(failure)

    with pytest.raises(GatewayError) as captured:
        await provider.analyze(complete_snapshot(), None)

    assert captured.value.code == code
    assert captured.value.status_code == status
    assert captured.value.retryable is retryable
    assert str(failure) not in captured.value.message


@pytest.mark.asyncio
async def test_native_analysis_marks_provider_rate_limit_retryable() -> None:
    request = httpx.Request("POST", "http://model.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    failure = httpx.HTTPStatusError("secret rate limit", request=request, response=response)
    provider, _client = build_provider(failure)

    with pytest.raises(GatewayError) as captured:
        await provider.analyze(complete_snapshot(), None)

    assert captured.value.code == "MODEL_RATE_LIMIT"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_native_analysis_normalizes_provider_configuration_failure() -> None:
    provider = NativeAnalysisProvider(
        provider_resolver=lambda: (_ for _ in ()).throw(ValueError("secret config")),
        structured_client=FakeStructuredClient(VALID_OUTPUT),
    )

    with pytest.raises(GatewayError) as captured:
        await provider.analyze(complete_snapshot(), None)

    assert captured.value.code == "PROVIDER_CONFIG_ERROR"
    assert captured.value.status_code == 503
    assert "secret config" not in captured.value.message
