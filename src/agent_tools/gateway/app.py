"""Optional FastAPI product Gateway for quant_trade integration."""

from __future__ import annotations

import uuid
from secrets import compare_digest
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .. import __version__
from ..tools import TOOL_NAMES
from .config import GatewaySettings
from .context import ContextCollector
from .errors import GatewayError
from .intelligence import GatewayIntelligenceService
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    CapabilitiesResponse,
    ChatRequest,
    ChatResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    GapNarrativeRequest,
    GapNarrativeResponse,
    HeadlineSentimentRequest,
    HeadlineSentimentResponse,
    SentimentSummaryRequest,
    SentimentSummaryResponse,
    ReviewRespondRequest,
    ReviewRespondResponse,
    TranslationRequest,
    TranslationResponse,
    WishInterpretationRequest,
    WishInterpretationResponse,
)
from .services import (
    AnalysisProvider,
    GatewayChatService,
    LegacyAnalysisProvider,
    NativeAnalysisProvider,
)


INTELLIGENCE_TASKS = (
    "headline_sentiment",
    "bundled_sentiment",
    "gap_narrative",
    "translation",
    "chat",
    "analysis",
    "wish_interpretation",
    "code_review",
    "review_response",
)


def _error_response(
    *,
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "retryable": retryable,
            }
        },
        headers={"X-Request-ID": request_id},
    )


def _contract_v1_response(request: Request, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request.state.request_id,
        "contract_version": "v1",
        **result,
    }


def _default_analysis_provider(
    orchestration_mode: str,
) -> NativeAnalysisProvider | LegacyAnalysisProvider:
    if orchestration_mode == "native":
        return NativeAnalysisProvider()
    if orchestration_mode == "legacy":
        return LegacyAnalysisProvider()
    raise ValueError(f"Orchestration mode is not implemented: {orchestration_mode}")


def create_app(
    *,
    settings: GatewaySettings | None = None,
    context_collector: ContextCollector | None = None,
    analysis_provider: AnalysisProvider | None = None,
    chat_service: GatewayChatService | None = None,
    intelligence_service: GatewayIntelligenceService | None = None,
) -> FastAPI:
    resolved_settings = settings or GatewaySettings.from_env()
    collector = context_collector or ContextCollector()
    provider = analysis_provider or _default_analysis_provider(
        resolved_settings.orchestration_mode
    )
    chat = chat_service or GatewayChatService()
    intelligence = intelligence_service or GatewayIntelligenceService()
    app = FastAPI(title="quant-trade-agent Gateway", version=__version__)

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        if resolved_settings.api_token and request.url.path != "/health":
            expected = f"Bearer {resolved_settings.api_token}"
            supplied = request.headers.get("Authorization", "")
            if not compare_digest(supplied, expected):
                return _error_response(
                    request_id=request_id,
                    code="UNAUTHORIZED",
                    message="缺少或无效的 Bearer token",
                    status_code=401,
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(GatewayError)
    async def handle_gateway_error(request: Request, exc: GatewayError) -> JSONResponse:
        return _error_response(
            request_id=request.state.request_id,
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            retryable=exc.retryable,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            request_id=request.state.request_id,
            code="VALIDATION_ERROR",
            message="请求参数不符合 v1 契约",
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(
            request_id=request.state.request_id,
            code="INTERNAL_ERROR",
            message="Gateway 内部错误",
            status_code=500,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/capabilities", response_model=CapabilitiesResponse)
    async def capabilities() -> dict[str, Any]:
        return {
            "contract_version": "v1",
            "version": __version__,
            "symbols": ["9984.T"],
            "tools": list(TOOL_NAMES),
            "providers": [
                "openai",
                "deepseek",
                "kimi",
                "minimax",
                "ollama",
                "custom",
            ],
            "orchestration_modes": {
                "active": resolved_settings.orchestration_mode,
                "available": ["native", "legacy"],
                "planned": [],
            },
            "transports": ["rest", "mcp-stdio", "mcp-streamable-http"],
            "intelligence_tasks": list(INTELLIGENCE_TASKS),
        }

    @app.post(
        "/v1/analyze",
        response_model=AnalyzeResponse,
        response_model_exclude_none=True,
    )
    async def analyze(request: Request, body: AnalyzeRequest) -> dict[str, Any]:
        snapshot = await collector.collect(body.symbol)
        result = await provider.analyze(snapshot, body.question)
        return {
            "request_id": request.state.request_id,
            "symbol": snapshot.symbol,
            "as_of": snapshot.as_of,
            **result,
        }

    @app.post("/v1/chat", response_model=ChatResponse)
    async def run_chat(request: Request, body: ChatRequest) -> dict[str, Any]:
        if len(body.history) > resolved_settings.max_history_messages:
            raise GatewayError(
                code="HISTORY_TOO_LONG",
                message="历史消息数量超过 Gateway 限制",
                status_code=422,
            )
        result = await chat.run(
            message=body.message,
            history=[item.model_dump() for item in body.history],
            symbol=body.symbol,
            allow_expensive_tools=body.allow_expensive_tools,
        )
        return {"request_id": request.state.request_id, **result}

    @app.post(
        "/v1/enrich/headlines/sentiment",
        response_model=HeadlineSentimentResponse,
    )
    async def enrich_headline_sentiment(
        request: Request,
        body: HeadlineSentimentRequest,
    ) -> dict[str, Any]:
        result = await intelligence.score_headlines(
            symbol=body.symbol,
            items=[item.model_dump() for item in body.items],
        )
        return _contract_v1_response(request, result)

    @app.post(
        "/v1/enrich/sentiment-summary",
        response_model=SentimentSummaryResponse,
    )
    async def enrich_sentiment_summary(
        request: Request,
        body: SentimentSummaryRequest,
    ) -> dict[str, Any]:
        result = await intelligence.summarize_sentiment(
            symbol=body.symbol,
            headlines=[headline.model_dump() for headline in body.headlines],
            price_context=body.price_context,
        )
        return _contract_v1_response(request, result)

    @app.post("/v1/narratives/gap", response_model=GapNarrativeResponse)
    async def generate_gap_narrative(
        request: Request,
        body: GapNarrativeRequest,
    ) -> dict[str, Any]:
        result = await intelligence.generate_gap_narrative(
            symbol=body.symbol,
            gap_pct=body.gap_pct,
            headlines=[headline.model_dump() for headline in body.headlines],
        )
        return _contract_v1_response(request, result)

    @app.post("/v1/translate", response_model=TranslationResponse)
    async def translate(
        request: Request,
        body: TranslationRequest,
    ) -> dict[str, Any]:
        result = await intelligence.translate(
            text=body.text,
            source_language=body.source_language,
            target_language=body.target_language,
        )
        return _contract_v1_response(request, result)

    @app.post(
        "/v1/interpret/wish",
        response_model=WishInterpretationResponse,
        response_model_exclude_none=True,
    )
    async def interpret_wish(
        request: Request,
        body: WishInterpretationRequest,
    ) -> dict[str, Any]:
        if len(body.history) > resolved_settings.max_history_messages:
            raise GatewayError(
                code="HISTORY_TOO_LONG",
                message="历史消息数量超过 Gateway 限制",
                status_code=422,
            )
        result = await intelligence.interpret_wish(
            message=body.message,
            history=[item.model_dump() for item in body.history],
        )
        return _contract_v1_response(request, result)

    @app.post("/v1/review/code", response_model=CodeReviewResponse)
    async def review_code(
        request: Request,
        body: CodeReviewRequest,
    ) -> dict[str, Any]:
        result = await intelligence.review_code(
            diff=body.diff,
            project_context=body.project_context,
        )
        return _contract_v1_response(request, result)

    @app.post("/v1/review/respond", response_model=ReviewRespondResponse)
    async def respond_to_review(
        request: Request,
        body: ReviewRespondRequest,
    ) -> dict[str, Any]:
        result = await intelligence.respond_to_review(
            message=body.message,
            context=body.context,
        )
        return _contract_v1_response(request, result)

    return app


def run_gateway(*, host: str = "127.0.0.1", port: int = 8010) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)
