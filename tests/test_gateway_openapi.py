from __future__ import annotations

import json
from pathlib import Path

from agent_tools.gateway.app import create_app
from agent_tools.gateway.config import GatewaySettings

CONTRACT_PATH = Path(__file__).parents[1] / "openapi" / "agent-gateway-v1.json"
REQUIRED_PRODUCT_ROUTES = {
    "/v1/analyze": "post",
    "/v1/chat": "post",
    "/v1/capabilities": "get",
    "/v1/enrich/headlines/sentiment": "post",
    "/v1/enrich/sentiment-summary": "post",
    "/v1/narratives/gap": "post",
    "/v1/translate": "post",
    "/v1/interpret/wish": "post",
    "/v1/review/code": "post",
    "/v1/review/respond": "post",
    "/v1/summarize/conversation": "post",
}


def test_snapshot_keeps_every_required_product_route() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    for path, method in REQUIRED_PRODUCT_ROUTES.items():
        assert method in snapshot["paths"][path]
        assert method in runtime["paths"][path]


def test_runtime_openapi_publishes_all_contract_v1_intelligence_paths() -> None:
    schema = create_app(settings=GatewaySettings()).openapi()

    expected = {
        "/v1/enrich/headlines/sentiment": (
            "HeadlineSentimentRequest",
            "HeadlineSentimentResponse",
        ),
        "/v1/enrich/sentiment-summary": (
            "SentimentSummaryRequest",
            "SentimentSummaryResponse",
        ),
        "/v1/narratives/gap": ("GapNarrativeRequest", "GapNarrativeResponse"),
        "/v1/translate": ("TranslationRequest", "TranslationResponse"),
        "/v1/interpret/wish": (
            "WishInterpretationRequest",
            "WishInterpretationResponse",
        ),
        "/v1/review/code": ("CodeReviewRequest", "CodeReviewResponse"),
        "/v1/review/respond": ("ReviewRespondRequest", "ReviewRespondResponse"),
        "/v1/summarize/conversation": (
            "ConversationSummaryRequest",
            "ConversationSummaryResponse",
        ),
    }
    for path, (request_model, response_model) in expected.items():
        operation = schema["paths"][path]["post"]
        request_ref = operation["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
        response_ref = operation["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        assert request_ref.endswith(f"/{request_model}")
        assert response_ref.endswith(f"/{response_model}")

    analyze = schema["paths"]["/v1/analyze"]["post"]
    assert analyze["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/AnalyzeRequest")
    assert analyze["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/AnalyzeResponse")


def test_contract_v1_models_forbid_unknown_request_fields() -> None:
    schema = create_app(settings=GatewaySettings()).openapi()

    for model_name in (
        "HeadlineSentimentRequest",
        "SentimentSummaryRequest",
        "GapNarrativeRequest",
        "TranslationRequest",
        "WishInterpretationRequest",
        "CodeReviewRequest",
        "ReviewRespondRequest",
        "ConversationSummaryRequest",
    ):
        assert schema["components"]["schemas"][model_name]["additionalProperties"] is False


def test_producer_openapi_snapshot_matches_runtime_intelligence_contract() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    assert snapshot["openapi"] == "3.1.0"
    assert snapshot["info"]["version"] == "v1"
    for path, snapshot_path in snapshot["paths"].items():
        methods = [method for method in snapshot_path if method in {"get", "post"}]
        assert len(methods) == 1
        method = methods[0]
        runtime_operation = runtime["paths"][path][method]
        snapshot_operation = snapshot_path[method]
        if "requestBody" in snapshot_operation:
            assert snapshot_operation["requestBody"] == runtime_operation["requestBody"]
        assert snapshot_operation["responses"]["200"] == runtime_operation["responses"]["200"]

    for name, snapshot_schema in snapshot["components"]["schemas"].items():
        runtime_schema = runtime["components"]["schemas"][name]
        assert runtime_schema == snapshot_schema


def test_producer_snapshot_includes_consumer_compatible_analyze_contract() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    snapshot_operation = snapshot["paths"]["/v1/analyze"]["post"]
    runtime_operation = runtime["paths"]["/v1/analyze"]["post"]
    assert snapshot_operation["requestBody"] == runtime_operation["requestBody"]
    assert snapshot_operation["responses"]["200"] == runtime_operation["responses"]["200"]
    for model_name in (
        "AnalyzeRequest",
        "AnalyzeResponse",
        "AnalysisDetails",
        "AnalysisDecision",
        "AnalysisProvenance",
    ):
        assert snapshot["components"]["schemas"][model_name] == runtime["components"][
            "schemas"
        ][model_name]


def test_producer_snapshot_includes_consumer_compatible_wish_contract() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    snapshot_operation = snapshot["paths"]["/v1/interpret/wish"]["post"]
    runtime_operation = runtime["paths"]["/v1/interpret/wish"]["post"]
    assert snapshot_operation["requestBody"] == runtime_operation["requestBody"]
    assert snapshot_operation["responses"]["200"] == runtime_operation["responses"]["200"]
    for model_name in (
        "HistoryMessage",
        "WishDetails",
        "WishInterpretationRequest",
        "WishInterpretationResponse",
    ):
        assert snapshot["components"]["schemas"][model_name] == runtime["components"][
            "schemas"
        ][model_name]


def test_snapshot_includes_exact_chat_and_capabilities_contracts() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    for path, method in (
        ("/v1/chat", "post"),
        ("/v1/capabilities", "get"),
    ):
        snapshot_operation = snapshot["paths"][path][method]
        runtime_operation = runtime["paths"][path][method]
        assert snapshot_operation.get("requestBody") == runtime_operation.get(
            "requestBody"
        )
        assert snapshot_operation["responses"]["200"] == runtime_operation["responses"][
            "200"
        ]

    for model_name in (
        "CapabilitiesResponse",
        "ChatRequest",
        "ChatResponse",
        "OrchestrationModes",
        "ConversationSummaryRequest",
        "ConversationSummaryResponse",
    ):
        assert snapshot["components"]["schemas"][model_name] == runtime["components"][
            "schemas"
        ][model_name]


def test_producer_snapshot_includes_exact_code_review_contracts() -> None:
    snapshot = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    runtime = create_app(settings=GatewaySettings()).openapi()

    for path in ("/v1/review/code", "/v1/review/respond"):
        snapshot_operation = snapshot["paths"][path]["post"]
        runtime_operation = runtime["paths"][path]["post"]
        assert snapshot_operation["requestBody"] == runtime_operation["requestBody"]
        assert snapshot_operation["responses"]["200"] == runtime_operation["responses"][
            "200"
        ]

    for model_name in (
        "CodeReviewRequest",
        "CodeReviewResponse",
        "ReviewRespondRequest",
        "ReviewRespondResponse",
    ):
        assert snapshot["components"]["schemas"][model_name] == runtime["components"][
            "schemas"
        ][model_name]
