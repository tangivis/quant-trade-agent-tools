from __future__ import annotations

from typing import Any

import httpx
import pytest

from agent_tools.gateway.errors import GatewayError
from agent_tools.gateway.intelligence import GatewayIntelligenceService
from agent_tools.providers import ProviderConfig

CONFIG = ProviderConfig(
    provider="deepseek",
    base_url="http://model.test/v1",
    model="deepseek-chat",
    api_key="fake-key",
)


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


def build_service(
    response: object,
) -> tuple[GatewayIntelligenceService, FakeStructuredClient]:
    client = FakeStructuredClient(response)
    return (
        GatewayIntelligenceService(
            provider_resolver=lambda: CONFIG,
            structured_client=client,
        ),
        client,
    )


COMPLETE_WISH = {
    "phase": "confirming",
    "title": "K线多周期",
    "type": "feature",
    "priority": "medium",
    "requirements": ["支持 1m/5m/15m 周期切换"],
    "summary": "K线图支持多周期切换",
}


@pytest.mark.asyncio
async def test_wish_clarifying_may_omit_structural_fields() -> None:
    service, client = build_service(
        {
            "reply": "请补充希望支持哪些K线周期。",
            "wish": {"phase": "clarifying"},
        }
    )

    result = await service.interpret_wish(
        message="我想改进K线图",
        history=[],
    )

    assert result == {
        "reply": "请补充希望支持哪些K线周期。",
        "wish": {"phase": "clarifying"},
        "provenance": {"provider": "deepseek", "model": "deepseek-chat"},
        "warnings": [],
    }
    assert client.calls[0]["task_name"] == "record_wish_interpretation"
    assert client.calls[0]["output_schema"]["additionalProperties"] is False
    assert client.calls[0]["output_schema"]["properties"]["wish"][
        "additionalProperties"
    ] is False


@pytest.mark.asyncio
async def test_wish_confirming_returns_complete_validated_payload() -> None:
    service, _client = build_service(
        {
            "reply": "我已整理完整需求，请确认提交。",
            "wish": COMPLETE_WISH,
        }
    )

    result = await service.interpret_wish(
        message="支持1m、5m和15m",
        history=[{"role": "user", "content": "我想改进K线图"}],
    )

    assert result["wish"] == COMPLETE_WISH
    assert result["reply"] == "我已整理完整需求，请确认提交。"


@pytest.mark.asyncio
async def test_wish_confirmed_reconstructs_full_payload_from_ordered_history() -> None:
    confirmed = {**COMPLETE_WISH, "phase": "confirmed"}
    service, client = build_service(
        {
            "reply": "需求已确认，交由产品创建Issue。",
            "wish": confirmed,
        }
    )
    history = [
        {"role": "user", "content": "我想改进K线图"},
        {"role": "assistant", "content": "请说明周期。"},
        {"role": "user", "content": "支持1m、5m和15m，优先级中。"},
        {"role": "assistant", "content": "已整理完整需求，请确认。"},
    ]

    result = await service.interpret_wish(message="确认", history=history)

    assert result["wish"] == confirmed
    assert client.calls[0]["user_payload"] == {
        "message": "确认",
        "history": history,
    }
    assert "完整" in client.calls[0]["system_prompt"]
    assert "历史" in client.calls[0]["system_prompt"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "phase": "executing"}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "type": "chore"}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "priority": "critical"}},
        {
            "reply": "请确认。",
            "wish": {key: value for key, value in COMPLETE_WISH.items() if key != "title"},
        },
        {"reply": "已确认。", "wish": {"phase": "confirmed"}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "requirements": []}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "requirements": ["  "]}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "title": "需" * 201}},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "summary": "需" * 4001}},
        {"reply": "回" * 4001, "wish": COMPLETE_WISH},
        {"reply": "please confirm", "wish": COMPLETE_WISH},
        {"reply": "请确认。", "wish": {**COMPLETE_WISH, "issue_body": "attack"}},
        {"reply": "请确认。", "wish": COMPLETE_WISH, "issue_url": "attack"},
        {
            "reply": "请补充。",
            "wish": {"phase": "clarifying", "type": "exploit"},
        },
    ],
)
async def test_wish_rejects_invalid_or_malicious_structured_output(
    response: dict[str, Any],
) -> None:
    service, _client = build_service(response)

    with pytest.raises(GatewayError) as captured:
        await service.interpret_wish(message="需求", history=[])

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert captured.value.status_code == 502
    assert captured.value.retryable is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "code", "status", "retryable"),
    [
        (httpx.TimeoutException("secret timeout"), "MODEL_TIMEOUT", 504, True),
        (ValueError("secret invalid"), "MODEL_RESPONSE_ERROR", 502, False),
    ],
)
async def test_wish_normalizes_provider_failures(
    failure: Exception,
    code: str,
    status: int,
    retryable: bool,
) -> None:
    service, _client = build_service(failure)

    with pytest.raises(GatewayError) as captured:
        await service.interpret_wish(message="需求", history=[])

    assert captured.value.code == code
    assert captured.value.status_code == status
    assert captured.value.retryable is retryable
    assert str(failure) not in captured.value.message


@pytest.mark.asyncio
async def test_wish_marks_provider_rate_limit_retryable() -> None:
    request = httpx.Request("POST", "http://model.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    failure = httpx.HTTPStatusError("secret limit", request=request, response=response)
    service, _client = build_service(failure)

    with pytest.raises(GatewayError) as captured:
        await service.interpret_wish(message="需求", history=[])

    assert captured.value.code == "MODEL_RATE_LIMIT"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_wish_normalizes_provider_configuration_failure() -> None:
    service = GatewayIntelligenceService(
        provider_resolver=lambda: (_ for _ in ()).throw(ValueError("secret config")),
        structured_client=FakeStructuredClient({}),
    )

    with pytest.raises(GatewayError) as captured:
        await service.interpret_wish(message="需求", history=[])

    assert captured.value.code == "PROVIDER_CONFIG_ERROR"
    assert captured.value.status_code == 503
    assert "secret config" not in captured.value.message
