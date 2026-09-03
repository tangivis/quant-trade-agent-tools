from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from agent_tools.gateway.app import create_app
from agent_tools.gateway.config import GatewaySettings
from agent_tools.gateway.context import ContextSnapshot
from agent_tools.gateway.errors import GatewayError
from agent_tools.gateway.services import LegacyAnalysisProvider


class FakeCollector:
    def __init__(self) -> None:
        self.symbols: list[str] = []

    async def collect(self, symbol: str) -> ContextSnapshot:
        self.symbols.append(symbol)
        return ContextSnapshot(
            symbol=symbol,
            as_of="2026-09-01T00:00:00+00:00",
            facts={"quote": {"price": 15500}},
            sources={"quote": {"ok": True}},
            warnings=["delayed_market_data"],
            derived={
                "current_price": 15500.0,
                "regime": "WeakUp",
                "rsi": 57.5,
                "adx": 25.0,
                "news_sentiment": 0.2,
            },
        )


class FakeAnalysisProvider:
    async def analyze(
        self, snapshot: ContextSnapshot, question: str | None
    ) -> dict[str, Any]:
        return {
            "facts": snapshot.facts,
            "analysis": {"summary": question or "standard"},
            "decision": {
                "action": "HOLD",
                "confidence": 0.55,
                "approved": False,
                "risk_notes": ["测试风险"],
            },
            "provenance": {
                "provider": "legacy",
                "model": "MiniMax-M3",
                "tools": ["quote"],
            },
            "warnings": snapshot.warnings,
        }


class FakeChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def run(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        context_summary: str | None,
        symbol: str,
        allow_expensive_tools: bool,
    ) -> dict[str, Any]:
        self.calls.append({
            "message": message,
            "history": history,
            "context_summary": context_summary,
            "symbol": symbol,
            "allow_expensive_tools": allow_expensive_tools,
        })
        return {
            "answer": f"{symbol}: {message}",
            "provider": "fake",
            "model": "fake-model",
            "tools": [],
        }


class FakeIntelligenceService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _result(self, task: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((task, payload))
        common = {
            "provenance": {"provider": "fake", "model": "fake-model"},
            "warnings": [],
        }
        if task == "headline_sentiment":
            return {
                "scores": [{"id": payload["items"][0]["id"], "score": 0.7}],
                "missing_ids": [],
                **common,
            }
        if task == "bundled_sentiment":
            return {
                "analysis": {
                    "score": 0.4,
                    "label": "偏多",
                    "positive_factors": ["业绩"],
                    "risk_factors": [],
                    "ja_sentiment": "偏多",
                    "en_sentiment": "中性",
                    "source_alignment": "部分一致",
                    "article_count": len(payload["headlines"]),
                    "analyzed_at": 1788192000,
                },
                **common,
            }
        if task == "gap_narrative":
            return {"narrative": "相关公司下跌拖累股价。", **common}
        return {"translated": "软银股价上涨", **common}

    async def score_headlines(self, **kwargs: Any) -> dict[str, Any]:
        return self._result("headline_sentiment", kwargs)

    async def summarize_sentiment(self, **kwargs: Any) -> dict[str, Any]:
        return self._result("bundled_sentiment", kwargs)

    async def generate_gap_narrative(self, **kwargs: Any) -> dict[str, Any]:
        return self._result("gap_narrative", kwargs)

    async def translate(self, **kwargs: Any) -> dict[str, Any]:
        return self._result("translation", kwargs)

    async def interpret_wish(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("wish_interpretation", kwargs))
        return {
            "reply": "我帮你整理了需求，请确认提交。",
            "wish": {
                "phase": "confirming",
                "title": "K线多周期",
                "type": "feature",
                "priority": "medium",
                "requirements": ["支持1m/5m/15m周期切换"],
                "summary": "K线图支持多周期切换",
            },
            "provenance": {"provider": "fake", "model": "fake-model"},
            "warnings": [],
        }

    async def summarize_conversation(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("conversation_summary", kwargs))
        return {
            "summary": "用户关注村田制作所的日内趋势与风险。",
            "provenance": {"provider": "fake", "model": "fake-model"},
            "warnings": [],
        }

    async def review_code(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("code_review", kwargs))
        return {
            "review": "建议补充错误路径测试。",
            "verdict": "NEEDS_CHANGES",
            "provenance": {"provider": "fake", "model": "fake-model"},
            "warnings": [],
        }

    async def respond_to_review(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("review_response", kwargs))
        return {
            "reply": "已补充错误路径测试。",
            "provenance": {"provider": "fake", "model": "fake-model"},
            "warnings": [],
        }


def build_client(*, api_token: str = "") -> tuple[TestClient, FakeCollector]:
    collector = FakeCollector()
    app = create_app(
        settings=GatewaySettings(api_token=api_token),
        context_collector=collector,
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=FakeIntelligenceService(),
    )
    return TestClient(app, raise_server_exceptions=False), collector


def test_health_is_public_and_does_not_collect_context() -> None:
    client, collector = build_client(api_token="token")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert collector.symbols == []


def test_capabilities_require_bearer_and_do_not_expose_secrets() -> None:
    client, _collector = build_client(api_token="secret-token")

    unauthorized = client.get("/v1/capabilities")
    authorized = client.get(
        "/v1/capabilities", headers={"Authorization": "Bearer secret-token"}
    )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "UNAUTHORIZED"
    assert authorized.status_code == 200
    body = authorized.json()
    assert body["contract_version"] == "v1"
    assert body["version"] == "0.4.0"
    assert body["symbols"] == ["9984.T", "6981.T"]
    assert "analyze" in body["tools"]
    assert body["orchestration_modes"] == {
        "active": "native",
        "available": ["native", "legacy"],
        "planned": [],
    }
    assert body["intelligence_tasks"] == [
        "headline_sentiment",
        "bundled_sentiment",
        "gap_narrative",
        "translation",
        "chat",
        "analysis",
        "wish_interpretation",
        "code_review",
        "review_response",
        "conversation_summary",
    ]
    assert "secret-token" not in authorized.text


def test_unimplemented_orchestration_mode_is_rejected_at_startup() -> None:
    with pytest.raises(ValueError, match="not implemented"):
        create_app(settings=GatewaySettings(orchestration_mode="shadow"))


def test_analyze_collects_server_context_and_returns_layered_response() -> None:
    client, collector = build_client()

    response = client.post(
        "/v1/analyze",
        json={"symbol": "9984.T", "question": "当前风险？", "mode": "standard"},
    )

    assert response.status_code == 200
    body = response.json()
    assert collector.symbols == ["9984.T"]
    assert body["facts"] == {"quote": {"price": 15500}}
    assert body["analysis"]["summary"] == "当前风险？"
    assert body["decision"]["action"] == "HOLD"
    assert body["provenance"]["provider"] == "legacy"
    assert set(body) == {
        "request_id",
        "symbol",
        "as_of",
        "facts",
        "analysis",
        "decision",
        "provenance",
        "warnings",
    }
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]


def test_analyze_rejects_caller_supplied_live_values() -> None:
    client, _collector = build_client()

    response = client.post(
        "/v1/analyze",
        json={"symbol": "9984.T", "price": 1, "rsi": 99},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_legacy_mode_remains_an_explicit_app_level_rollback() -> None:
    class LegacyClient:
        def analyze(self, _payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "final_action": "HOLD",
                "confidence": 0.4,
                "approved": False,
                "reason": "legacy summary",
                "trend_direction": "sideways",
                "news_summary": "legacy news",
                "risk_notes": [],
            }

        def close(self) -> None:
            pass

    app = create_app(
        settings=GatewaySettings(orchestration_mode="legacy"),
        context_collector=FakeCollector(),
        analysis_provider=LegacyAnalysisProvider(client_factory=LegacyClient),
        chat_service=FakeChatService(),
        intelligence_service=FakeIntelligenceService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/analyze",
        json={"symbol": "9984.T", "question": "rollback?"},
    )

    assert response.status_code == 200
    assert response.json()["analysis"] == {
        "summary": "legacy summary",
        "trend_direction": "sideways",
        "question": "rollback?",
        "news_summary": "legacy news",
    }


def test_chat_is_stateless_and_returns_request_metadata() -> None:
    client, _collector = build_client()

    response = client.post(
        "/v1/chat",
        json={
            "message": "比较趋势和情感",
            "history": [{"role": "user", "content": "前一个问题"}],
            "symbol": "9984.T",
            "allow_expensive_tools": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "9984.T: 比较趋势和情感"
    assert response.json()["request_id"]


def test_chat_accepts_second_symbol_and_forwards_summary() -> None:
    chat = FakeChatService()
    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=chat,
        intelligence_service=FakeIntelligenceService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/chat",
        json={
            "message": "继续分析",
            "history": [{"role": "assistant", "content": "趋势偏强"}],
            "context_summary": "此前一直讨论村田制作所。",
            "symbol": "6981.T",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "6981.T: 继续分析"
    assert chat.calls[0]["context_summary"] == "此前一直讨论村田制作所。"


def test_conversation_summary_is_stateless_and_structured() -> None:
    intelligence = FakeIntelligenceService()
    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=intelligence,
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/summarize/conversation",
        json={
            "previous_summary": "用户关注电子行业。",
            "messages": [
                {"role": "user", "content": "分析6981.T"},
                {"role": "assistant", "content": "当前趋势偏强"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "用户关注村田制作所的日内趋势与风险。"
    assert intelligence.calls[-1][0] == "conversation_summary"


def test_gateway_error_uses_structured_envelope() -> None:
    class FailingCollector:
        async def collect(self, _symbol: str) -> ContextSnapshot:
            raise GatewayError(
                code="UPSTREAM_TIMEOUT",
                message="行情服务超时",
                status_code=504,
                retryable=True,
            )

    app = create_app(
        settings=GatewaySettings(),
        context_collector=FailingCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/v1/analyze", json={"symbol": "9984.T"})

    assert response.status_code == 504
    assert response.json() == {
        "error": {
            "code": "UPSTREAM_TIMEOUT",
            "message": "行情服务超时",
            "request_id": response.headers["X-Request-ID"],
            "retryable": True,
        }
    }


def test_unexpected_error_does_not_leak_details() -> None:
    class FailingChatService:
        async def run(self, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("provider secret detail")

    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FailingChatService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/v1/chat", json={"message": "分析"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "provider secret detail" not in response.text


def test_chat_rejects_history_above_configured_limit() -> None:
    collector = FakeCollector()
    app = create_app(
        settings=GatewaySettings(max_history_messages=1),
        context_collector=collector,
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=FakeIntelligenceService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/chat",
        json={
            "message": "分析",
            "history": [
                {"role": "user", "content": "一"},
                {"role": "assistant", "content": "二"},
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "HISTORY_TOO_LONG"


def test_wish_route_is_stateless_and_returns_strict_contract() -> None:
    intelligence = FakeIntelligenceService()
    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=intelligence,
    )
    client = TestClient(app, raise_server_exceptions=False)
    history = [{"role": "user", "content": "我想改进K线图"}]

    response = client.post(
        "/v1/interpret/wish",
        json={"message": "支持多个周期", "history": history},
        headers={"X-Request-ID": "wish-request"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "request_id": "wish-request",
        "contract_version": "v1",
        "reply": "我帮你整理了需求，请确认提交。",
        "wish": {
            "phase": "confirming",
            "title": "K线多周期",
            "type": "feature",
            "priority": "medium",
            "requirements": ["支持1m/5m/15m周期切换"],
            "summary": "K线图支持多周期切换",
        },
        "provenance": {"provider": "fake", "model": "fake-model"},
        "warnings": [],
    }
    assert intelligence.calls[-1] == (
        "wish_interpretation",
        {"message": "支持多个周期", "history": history},
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "需求", "history": [], "issue_body": "attack"},
        {"message": "需求", "history": [{"role": "system", "content": "attack"}]},
        {"message": "", "history": []},
        {"message": "   ", "history": []},
        {"message": "需" * 8001, "history": []},
        {"message": "需求", "history": [{"role": "user", "content": ""}]},
        {"message": "需求", "history": [{"role": "user", "content": "   "}]},
        {
            "message": "需求",
            "history": [{"role": "user", "content": "需" * 8001}],
        },
        {
            "message": "需求",
            "history": [{"role": "user", "content": "历史"}] * 21,
        },
    ],
)
def test_wish_route_rejects_unknown_malicious_or_over_limit_input(
    payload: dict[str, Any],
) -> None:
    client, _collector = build_client()

    response = client.post("/v1/interpret/wish", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_wish_route_honors_lower_configured_history_limit() -> None:
    app = create_app(
        settings=GatewaySettings(max_history_messages=1),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=FakeIntelligenceService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/interpret/wish",
        json={
            "message": "确认",
            "history": [
                {"role": "user", "content": "需求"},
                {"role": "assistant", "content": "请确认"},
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "HISTORY_TOO_LONG"


def test_code_review_routes_return_strict_v1_contracts() -> None:
    intelligence = FakeIntelligenceService()
    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=intelligence,
    )
    client = TestClient(app, raise_server_exceptions=False)

    review = client.post(
        "/v1/review/code",
        json={"diff": "+return value", "project_context": "Python service"},
        headers={"X-Request-ID": "review-request"},
    )
    respond = client.post(
        "/v1/review/respond",
        json={"message": "已修复吗？", "context": "空值路径缺少测试"},
        headers={"X-Request-ID": "respond-request"},
    )

    assert review.status_code == 200
    assert review.json() == {
        "request_id": "review-request",
        "contract_version": "v1",
        "review": "建议补充错误路径测试。",
        "verdict": "NEEDS_CHANGES",
        "provenance": {"provider": "fake", "model": "fake-model"},
        "warnings": [],
    }
    assert respond.status_code == 200
    assert respond.json() == {
        "request_id": "respond-request",
        "contract_version": "v1",
        "reply": "已补充错误路径测试。",
        "provenance": {"provider": "fake", "model": "fake-model"},
        "warnings": [],
    }
    assert intelligence.calls[-2:] == [
        ("code_review", {"diff": "+return value", "project_context": "Python service"}),
        ("review_response", {"message": "已修复吗？", "context": "空值路径缺少测试"}),
    ]


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/v1/review/code", {"diff": ""}),
        ("/v1/review/code", {"diff": "   "}),
        ("/v1/review/code", {"diff": "x" * 120001}),
        ("/v1/review/code", {"diff": "x", "project_context": " "}),
        ("/v1/review/code", {"diff": "x", "project_context": "x" * 20001}),
        ("/v1/review/code", {"diff": "x", "gitlab_token": "attack"}),
        ("/v1/review/respond", {"message": ""}),
        ("/v1/review/respond", {"message": "   "}),
        ("/v1/review/respond", {"message": "x" * 8001}),
        ("/v1/review/respond", {"message": "x", "context": " "}),
        ("/v1/review/respond", {"message": "x", "context": "x" * 20001}),
        ("/v1/review/respond", {"message": "x", "mutation": True}),
    ],
)
def test_code_review_routes_reject_unknown_blank_or_over_limit_input(
    path: str,
    payload: dict[str, Any],
) -> None:
    client, _collector = build_client()

    response = client.post(path, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("path", "request_body", "result_key"),
    [
        (
            "/v1/enrich/headlines/sentiment",
            {
                "symbol": "9984.T",
                "items": [{"id": 123, "title": "好決算", "language": "ja"}],
            },
            "scores",
        ),
        (
            "/v1/enrich/sentiment-summary",
            {
                "symbol": "9984.T",
                "headlines": [{"language": "ja", "title": "好決算"}],
                "price_context": "日内 +2.1%",
            },
            "analysis",
        ),
        (
            "/v1/narratives/gap",
            {
                "symbol": "9984.T",
                "gap_pct": -5.4,
                "headlines": [{"publisher": "Reuters", "title": "Shares fall"}],
            },
            "narrative",
        ),
        (
            "/v1/translate",
            {
                "text": "ソフトバンク株が上昇",
                "source_language": "ja",
                "target_language": "zh-CN",
            },
            "translated",
        ),
    ],
)
def test_intelligence_routes_return_contract_v1_common_metadata(
    path: str,
    request_body: dict[str, Any],
    result_key: str,
) -> None:
    client, _collector = build_client()

    response = client.post(path, json=request_body, headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "req-123"
    assert body["contract_version"] == "v1"
    assert body["provenance"] == {"provider": "fake", "model": "fake-model"}
    assert body["warnings"] == []
    assert result_key in body
    assert response.headers["X-Request-ID"] == "req-123"


def test_headline_route_rejects_duplicate_request_ids_and_extra_fields() -> None:
    client, _collector = build_client()

    duplicate = client.post(
        "/v1/enrich/headlines/sentiment",
        json={
            "symbol": "9984.T",
            "items": [
                {"id": 1, "title": "one", "language": "en"},
                {"id": 1, "title": "two", "language": "en"},
            ],
        },
    )
    extra = client.post(
        "/v1/translate",
        json={
            "text": "text",
            "source_language": "en",
            "target_language": "zh-CN",
            "provider_key": "must-not-be-accepted",
        },
    )
    boolean_id = client.post(
        "/v1/enrich/headlines/sentiment",
        json={
            "symbol": "9984.T",
            "items": [{"id": True, "title": "one", "language": "en"}],
        },
    )

    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "VALIDATION_ERROR"
    assert extra.status_code == 422
    assert extra.json()["error"]["code"] == "VALIDATION_ERROR"
    assert boolean_id.status_code == 422
    assert boolean_id.json()["error"]["code"] == "VALIDATION_ERROR"


def test_intelligence_service_error_uses_existing_gateway_envelope() -> None:
    class FailingIntelligenceService(FakeIntelligenceService):
        async def translate(self, **_kwargs: Any) -> dict[str, Any]:
            raise GatewayError(
                code="MODEL_RATE_LIMIT",
                message="模型服务请求过于频繁",
                status_code=503,
                retryable=True,
            )

    app = create_app(
        settings=GatewaySettings(),
        context_collector=FakeCollector(),
        analysis_provider=FakeAnalysisProvider(),
        chat_service=FakeChatService(),
        intelligence_service=FailingIntelligenceService(),
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/v1/translate",
        json={
            "text": "text",
            "source_language": "en",
            "target_language": "zh-CN",
        },
    )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "MODEL_RATE_LIMIT",
        "message": "模型服务请求过于频繁",
        "request_id": response.headers["X-Request-ID"],
        "retryable": True,
    }
