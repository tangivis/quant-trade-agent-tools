"""Pydantic contracts for the product REST Gateway."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class StrictContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalyzeRequest(StrictContractModel):

    symbol: Literal["9984.T"] = "9984.T"
    question: str | None = Field(default=None, max_length=2000)
    mode: Literal["standard"] = "standard"


class AnalysisDetails(StrictContractModel):
    summary: str = Field(max_length=2000)
    trend_direction: str | None = Field(default=None, max_length=64)
    question: str | None = Field(default=None, max_length=2000)
    news_summary: str | None = Field(default=None, max_length=2000)


class AnalysisDecision(StrictContractModel):
    action: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    approved: bool
    risk_notes: list[str]


class AnalysisProvenance(StrictContractModel):
    provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=256)
    tools: list[str]


class AnalyzeResponse(StrictContractModel):
    request_id: str
    symbol: Literal["9984.T"]
    as_of: str
    facts: dict[str, Any]
    analysis: AnalysisDetails
    decision: AnalysisDecision
    provenance: AnalysisProvenance
    warnings: list[str]


class HistoryMessage(StrictContractModel):

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(StrictContractModel):

    message: str = Field(min_length=1, max_length=8000)
    history: list[HistoryMessage] = Field(default_factory=list)
    symbol: Literal["9984.T"] = "9984.T"
    allow_expensive_tools: bool = False


class ChatResponse(StrictContractModel):
    request_id: str
    answer: str
    provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=256)
    tools: list[str]


class OrchestrationModes(StrictContractModel):
    active: Literal["native", "legacy"]
    available: list[Literal["native", "legacy"]]
    planned: list[str]


class CapabilitiesResponse(StrictContractModel):
    contract_version: Literal["v1"] = "v1"
    version: str
    symbols: list[str]
    tools: list[str]
    providers: list[str]
    orchestration_modes: OrchestrationModes
    transports: list[str]
    intelligence_tasks: list[str]


class WishInterpretationRequest(StrictContractModel):
    message: str = Field(min_length=1, max_length=8000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def text_must_not_be_blank(self) -> WishInterpretationRequest:
        if not self.message.strip() or any(
            not item.content.strip() for item in self.history
        ):
            raise ValueError("wish message and history content must not be blank")
        return self


class Provenance(StrictContractModel):
    provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=256)


WishPhase = Literal["clarifying", "confirming", "confirmed"]
WishType = Literal["feature", "bug", "refactor"]
WishPriority = Literal["low", "medium", "high", "urgent"]
WishRequirement = Annotated[str, Field(min_length=1, max_length=1000)]


class WishDetails(StrictContractModel):
    phase: WishPhase
    title: str | None = Field(default=None, min_length=1, max_length=200)
    type: WishType | None = None
    priority: WishPriority | None = None
    requirements: list[WishRequirement] | None = Field(
        default=None, min_length=1, max_length=20
    )
    summary: str | None = Field(default=None, min_length=1, max_length=4000)

    @model_validator(mode="after")
    def complete_phases_require_full_payload(self) -> WishDetails:
        if self.phase == "clarifying":
            return self
        if (
            self.title is None
            or self.type is None
            or self.priority is None
            or not self.requirements
            or self.summary is None
        ):
            raise ValueError("confirming and confirmed wishes require a full payload")
        return self


class WishInterpretationResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    reply: str = Field(min_length=1, max_length=4000)
    wish: WishDetails
    provenance: Provenance
    warnings: list[str]


class HeadlineItem(StrictContractModel):
    id: StrictInt
    title: str = Field(min_length=1, max_length=2000)
    language: str = Field(min_length=2, max_length=16)


class HeadlineSentimentRequest(StrictContractModel):
    symbol: Literal["9984.T"] = "9984.T"
    items: list[HeadlineItem] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def ids_must_be_unique(self) -> HeadlineSentimentRequest:
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("headline item IDs must be unique")
        return self


class HeadlineScore(StrictContractModel):
    id: StrictInt
    score: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)


class HeadlineSentimentResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    scores: list[HeadlineScore]
    missing_ids: list[StrictInt]
    provenance: Provenance
    warnings: list[str]


class SentimentHeadline(StrictContractModel):
    language: str = Field(min_length=2, max_length=16)
    title: str = Field(min_length=1, max_length=2000)


class SentimentSummaryRequest(StrictContractModel):
    symbol: Literal["9984.T"] = "9984.T"
    headlines: list[SentimentHeadline] = Field(min_length=1, max_length=100)
    price_context: str = Field(min_length=1, max_length=2000)


SentimentLabel = Literal["看涨", "偏多", "中性", "偏空", "看跌"]
SourceAlignment = Literal["一致", "部分一致", "分歧", "信息不足"]


class SentimentAnalysis(StrictContractModel):
    score: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    label: SentimentLabel
    positive_factors: list[str]
    risk_factors: list[str]
    ja_sentiment: SentimentLabel
    en_sentiment: SentimentLabel
    source_alignment: SourceAlignment
    article_count: int = Field(ge=0)
    analyzed_at: int = Field(ge=0)


class SentimentSummaryResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    analysis: SentimentAnalysis
    provenance: Provenance
    warnings: list[str]


class GapHeadline(StrictContractModel):
    publisher: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=2000)


class GapNarrativeRequest(StrictContractModel):
    symbol: Literal["9984.T"] = "9984.T"
    gap_pct: float = Field(allow_inf_nan=False)
    headlines: list[GapHeadline] = Field(min_length=1, max_length=100)


class GapNarrativeResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    narrative: str = Field(min_length=1, max_length=60)
    provenance: Provenance
    warnings: list[str]


class TranslationRequest(StrictContractModel):
    text: str = Field(min_length=1, max_length=8000)
    source_language: str = Field(min_length=2, max_length=16)
    target_language: Literal["zh-CN"] = "zh-CN"


class TranslationResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    translated: str = Field(min_length=1, max_length=8000)
    provenance: Provenance
    warnings: list[str]


class CodeReviewRequest(StrictContractModel):
    diff: str = Field(min_length=1, max_length=120000)
    project_context: str | None = Field(default=None, min_length=1, max_length=20000)

    @model_validator(mode="after")
    def text_must_not_be_blank(self) -> CodeReviewRequest:
        if not self.diff.strip() or (
            self.project_context is not None and not self.project_context.strip()
        ):
            raise ValueError("code review input must not be blank")
        return self


ReviewVerdict = Literal["LGTM", "NEEDS_CHANGES"]


class CodeReviewResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    review: str = Field(min_length=1, max_length=12000)
    verdict: ReviewVerdict
    provenance: Provenance
    warnings: list[str]


class ReviewRespondRequest(StrictContractModel):
    message: str = Field(min_length=1, max_length=8000)
    context: str | None = Field(default=None, min_length=1, max_length=20000)

    @model_validator(mode="after")
    def text_must_not_be_blank(self) -> ReviewRespondRequest:
        if not self.message.strip() or (
            self.context is not None and not self.context.strip()
        ):
            raise ValueError("review response input must not be blank")
        return self


class ReviewRespondResponse(StrictContractModel):
    request_id: str
    contract_version: Literal["v1"] = "v1"
    reply: str = Field(min_length=1, max_length=8000)
    provenance: Provenance
    warnings: list[str]
