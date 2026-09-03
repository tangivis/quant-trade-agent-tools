from __future__ import annotations

import inspect
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


@pytest.mark.asyncio
async def test_code_review_uses_forced_schema_and_returns_validated_contract() -> None:
    service, client = build_service(
        {"review": "空值路径缺少测试，建议补充回归用例。", "verdict": "NEEDS_CHANGES"}
    )
    diff = "diff --git a/a.py b/a.py\n+return value"

    result = await service.review_code(
        diff=diff,
        project_context="Python service; errors use GatewayError.",
    )

    assert result == {
        "review": "空值路径缺少测试，建议补充回归用例。",
        "verdict": "NEEDS_CHANGES",
        "provenance": {"provider": "deepseek", "model": "deepseek-chat"},
        "warnings": [],
    }
    call = client.calls[0]
    assert call["task_name"] == "record_code_review"
    assert call["user_payload"] == {
        "diff": diff,
        "project_context": "Python service; errors use GatewayError.",
    }
    assert call["output_schema"] == {
        "type": "object",
        "properties": {
            "review": {"type": "string", "minLength": 1, "maxLength": 12000},
            "verdict": {"type": "string", "enum": ["LGTM", "NEEDS_CHANGES"]},
        },
        "required": ["review", "verdict"],
        "additionalProperties": False,
    }
    assert "untrusted" in call["system_prompt"].lower()
    assert "never execute" in call["system_prompt"].lower()


@pytest.mark.asyncio
async def test_review_response_is_stateless_and_structured() -> None:
    service, client = build_service({"reply": "同意，该问题已在当前 diff 中修复。"})

    result = await service.respond_to_review(
        message="这个空值问题已经修复了吗？",
        context="Reviewer requested a null-path regression test.",
    )

    assert result == {
        "reply": "同意，该问题已在当前 diff 中修复。",
        "provenance": {"provider": "deepseek", "model": "deepseek-chat"},
        "warnings": [],
    }
    call = client.calls[0]
    assert call["task_name"] == "record_review_response"
    assert call["user_payload"] == {
        "message": "这个空值问题已经修复了吗？",
        "context": "Reviewer requested a null-path regression test.",
    }
    assert call["output_schema"]["additionalProperties"] is False
    assert call["output_schema"]["required"] == ["reply"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {"review": "ok", "verdict": "APPROVED"},
        {"review": "ok"},
        {"review": "ok", "verdict": "LGTM", "approval": True},
        {"review": "   ", "verdict": "LGTM"},
        {"review": "x" * 12001, "verdict": "LGTM"},
        {"review": 1, "verdict": "LGTM"},
    ],
)
async def test_code_review_rejects_invalid_structured_output(
    response: dict[str, Any],
) -> None:
    service, _client = build_service(response)

    with pytest.raises(GatewayError) as captured:
        await service.review_code(diff="diff", project_context=None)

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert captured.value.status_code == 502


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {},
        {"reply": "", "status": "sent"},
        {"reply": "   "},
        {"reply": "x" * 8001},
        {"reply": ["not text"]},
    ],
)
async def test_review_response_rejects_invalid_structured_output(
    response: dict[str, Any],
) -> None:
    service, _client = build_service(response)

    with pytest.raises(GatewayError) as captured:
        await service.respond_to_review(message="reply", context=None)

    assert captured.value.code == "MODEL_RESPONSE_ERROR"
    assert captured.value.status_code == 502


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failure", "code", "status", "retryable"),
    [
        (httpx.TimeoutException("secret timeout"), "MODEL_TIMEOUT", 504, True),
        (ValueError("secret invalid"), "MODEL_RESPONSE_ERROR", 502, False),
    ],
)
async def test_code_review_normalizes_provider_failures(
    failure: Exception,
    code: str,
    status: int,
    retryable: bool,
) -> None:
    service, _client = build_service(failure)

    with pytest.raises(GatewayError) as captured:
        await service.review_code(diff="diff", project_context=None)

    assert captured.value.code == code
    assert captured.value.status_code == status
    assert captured.value.retryable is retryable
    assert str(failure) not in captured.value.message


@pytest.mark.asyncio
async def test_review_response_marks_provider_rate_limit_retryable() -> None:
    request = httpx.Request("POST", "http://model.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    service, _client = build_service(
        httpx.HTTPStatusError("secret limit", request=request, response=response)
    )

    with pytest.raises(GatewayError) as captured:
        await service.respond_to_review(message="reply", context=None)

    assert captured.value.code == "MODEL_RATE_LIMIT"
    assert captured.value.status_code == 503
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_code_review_normalizes_provider_configuration_failure() -> None:
    service = GatewayIntelligenceService(
        provider_resolver=lambda: (_ for _ in ()).throw(ValueError("secret config")),
        structured_client=FakeStructuredClient({}),
    )

    with pytest.raises(GatewayError) as captured:
        await service.review_code(diff="diff", project_context=None)

    assert captured.value.code == "PROVIDER_CONFIG_ERROR"
    assert captured.value.status_code == 503
    assert "secret config" not in captured.value.message


def test_code_review_methods_contain_no_mutation_client_or_agent_loop() -> None:
    source = "\n".join(
        (
            inspect.getsource(GatewayIntelligenceService.review_code),
            inspect.getsource(GatewayIntelligenceService.respond_to_review),
        )
    ).lower()

    for forbidden in (
        "gitlab",
        "issue",
        "merge_request",
        "database",
        "order",
        "cancel",
        "broker",
        "subprocess",
        "openai-compatible-agent",
    ):
        assert forbidden not in source
