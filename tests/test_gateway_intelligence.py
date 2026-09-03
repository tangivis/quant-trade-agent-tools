from __future__ import annotations

import json
import math
from typing import Any

import httpx
import pytest

from agent_tools.gateway.errors import GatewayError
from agent_tools.gateway.intelligence import (
    GatewayIntelligenceService,
    OpenAICompatibleStructuredClient,
)
from agent_tools.providers import ProviderConfig


CONFIG = ProviderConfig(
    provider="fake",
    base_url="http://model.test/v1",
    model="fake-model",
    api_key="fake-key",
)


class FakeStructuredClient:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        assert isinstance(response, dict)
        return response


def build_service(
    *responses: object,
) -> tuple[GatewayIntelligenceService, FakeStructuredClient]:
    client = FakeStructuredClient(*responses)
    service = GatewayIntelligenceService(
        provider_resolver=lambda: CONFIG,
        structured_client=client,
        clock=lambda: 1788192000,
    )
    return service, client


@pytest.mark.asyncio
async def test_headline_scores_preserve_request_order_and_clamp_finite_values() -> None:
    service, client = build_service(
        {"scores": [{"id": 2, "score": 4.5}, {"id": 1, "score": -1.25}]}
    )

    result = await service.score_headlines(
        symbol="9984.T",
        items=[
            {"id": 1, "title": "bad", "language": "en"},
            {"id": 2, "title": "good", "language": "en"},
        ],
    )

    assert result == {
        "scores": [{"id": 1, "score": -1.0}, {"id": 2, "score": 1.0}],
        "missing_ids": [],
        "provenance": {"provider": "fake", "model": "fake-model"},
        "warnings": [],
    }
    assert len(client.calls) == 1
    assert client.calls[0]["task_name"] == "record_headline_sentiment"


@pytest.mark.asyncio
async def test_headline_scores_repair_only_missing_ids_once() -> None:
    service, client = build_service(
        {"scores": [{"id": 1, "score": 0.2}]},
        {"scores": [{"id": 3, "score": -0.4}, {"id": 2, "score": 0.6}]},
    )

    result = await service.score_headlines(
        symbol="9984.T",
        items=[
            {"id": 1, "title": "one", "language": "en"},
            {"id": 2, "title": "two", "language": "en"},
            {"id": 3, "title": "three", "language": "en"},
        ],
    )

    assert result["scores"] == [
        {"id": 1, "score": 0.2},
        {"id": 2, "score": 0.6},
        {"id": 3, "score": -0.4},
    ]
    assert result["missing_ids"] == []
    assert len(client.calls) == 2
    assert [item["id"] for item in client.calls[1]["user_payload"]["items"]] == [2, 3]


@pytest.mark.asyncio
async def test_headline_scores_report_ids_still_missing_after_one_repair() -> None:
    service, client = build_service(
        {"scores": [{"id": 1, "score": 0.2}]},
        {"scores": []},
    )

    result = await service.score_headlines(
        symbol="9984.T",
        items=[
            {"id": 1, "title": "one", "language": "en"},
            {"id": 2, "title": "two", "language": "en"},
        ],
    )

    assert result["scores"] == [{"id": 1, "score": 0.2}]
    assert result["missing_ids"] == [2]
    assert result["warnings"] == ["missing_ids_after_repair"]
    assert len(client.calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {"scores": [{"id": 999, "score": 0.1}]},
        {"scores": [{"id": 1, "score": 0.1}, {"id": 1, "score": 0.2}]},
        {"scores": [{"id": 1, "score": math.inf}]},
    ],
)
async def test_headline_scores_reject_invalid_structured_ids_or_scores(
    response: dict[str, Any],
) -> None:
    service, _client = build_service(response)

    with pytest.raises(GatewayError) as captured:
        await service.score_headlines(
            symbol="9984.T",
            items=[{"id": 1, "title": "one", "language": "en"}],
        )

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert captured.value.status_code == 502


@pytest.mark.asyncio
async def test_sentiment_summary_uses_server_metadata_and_clamps_score() -> None:
    service, _client = build_service(
        {
            "score": 1.4,
            "label": "偏多",
            "positive_factors": ["业绩改善"],
            "risk_factors": ["波动率较高"],
            "ja_sentiment": "偏多",
            "en_sentiment": "中性",
            "source_alignment": "部分一致",
        }
    )

    result = await service.summarize_sentiment(
        symbol="9984.T",
        headlines=[
            {"language": "ja", "title": "好決算"},
            {"language": "en", "title": "Shares gain"},
        ],
        price_context="日内 +2.1%",
    )

    assert result["analysis"] == {
        "score": 1.0,
        "label": "偏多",
        "positive_factors": ["业绩改善"],
        "risk_factors": ["波动率较高"],
        "ja_sentiment": "偏多",
        "en_sentiment": "中性",
        "source_alignment": "部分一致",
        "article_count": 2,
        "analyzed_at": 1788192000,
    }
    assert result["warnings"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "narrative",
    [
        "软银股价受相关公司下跌影响。" * 5,
        "消息偏弱，建议卖出并设置止损。",
        "后市将继续下跌。",
    ],
)
async def test_gap_narrative_rejects_length_outlook_or_trading_advice(
    narrative: str,
) -> None:
    service, _client = build_service({"narrative": narrative})

    with pytest.raises(GatewayError) as captured:
        await service.generate_gap_narrative(
            symbol="9984.T",
            gap_pct=-5.4,
            headlines=[{"publisher": "Reuters", "title": "Shares fall"}],
        )

    assert captured.value.code == "MODEL_RESPONSE_ERROR"


@pytest.mark.asyncio
async def test_gap_narrative_and_translation_return_normalized_results() -> None:
    service, client = build_service(
        {"narrative": "相关公司股价下跌拖累软银表现。"},
        {"translated": "软银股价上涨"},
    )

    narrative = await service.generate_gap_narrative(
        symbol="9984.T",
        gap_pct=-5.4,
        headlines=[{"publisher": "Reuters", "title": "Shares fall"}],
    )
    translated = await service.translate(
        text="ソフトバンク株が上昇",
        source_language="ja",
        target_language="zh-CN",
    )

    assert narrative["narrative"] == "相关公司股价下跌拖累软银表现。"
    assert translated["translated"] == "软银股价上涨"
    assert narrative["provenance"] == translated["provenance"] == {
        "provider": "fake",
        "model": "fake-model",
    }
    assert [call["task_name"] for call in client.calls] == [
        "record_gap_narrative",
        "record_translation",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "expected_code", "expected_status", "retryable"),
    [
        (httpx.TimeoutException("timeout"), "MODEL_TIMEOUT", 504, True),
        (httpx.ConnectError("down"), "MODEL_ERROR", 502, True),
        (ValueError("invalid output"), "MODEL_RESPONSE_ERROR", 502, False),
    ],
)
async def test_provider_failures_use_gateway_error_contract(
    failure: Exception,
    expected_code: str,
    expected_status: int,
    retryable: bool,
) -> None:
    service, _client = build_service(failure)

    with pytest.raises(GatewayError) as captured:
        await service.translate(
            text="text", source_language="en", target_language="zh-CN"
        )

    assert captured.value.code == expected_code
    assert captured.value.status_code == expected_status
    assert captured.value.retryable is retryable
    assert str(failure) not in captured.value.message


@pytest.mark.asyncio
async def test_provider_rate_limit_is_retryable() -> None:
    request = httpx.Request("POST", "http://model.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    failure = httpx.HTTPStatusError("rate limited secret", request=request, response=response)
    service, _client = build_service(failure)

    with pytest.raises(GatewayError) as captured:
        await service.translate(
            text="text", source_language="en", target_language="zh-CN"
        )

    assert captured.value.code == "MODEL_RATE_LIMIT"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_provider_configuration_failure_is_normalized() -> None:
    service = GatewayIntelligenceService(
        provider_resolver=lambda: (_ for _ in ()).throw(ValueError("secret config")),
        structured_client=FakeStructuredClient(),
    )

    with pytest.raises(GatewayError) as captured:
        await service.translate(
            text="text", source_language="en", target_language="zh-CN"
        )

    assert captured.value.code == "PROVIDER_CONFIG_ERROR"
    assert "secret config" not in captured.value.message


def test_openai_compatible_client_forces_named_tool_and_parses_arguments() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer fake-key"
        payload = json.loads(request.content)
        assert payload["tool_choice"] == {
            "type": "function",
            "function": {"name": "record_translation"},
        }
        assert payload["tools"][0]["function"]["name"] == "record_translation"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "record_translation",
                                        "arguments": '{"translated":"译文"}',
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = OpenAICompatibleStructuredClient(
        transport=httpx.MockTransport(handler)
    )

    result = client.complete(
        config=CONFIG,
        task_name="record_translation",
        task_description="return translation",
        system_prompt="translate",
        user_payload={"text": "text"},
        output_schema={
            "type": "object",
            "properties": {"translated": {"type": "string"}},
            "required": ["translated"],
            "additionalProperties": False,
        },
        max_tokens=500,
    )

    assert result == {"translated": "译文"}
