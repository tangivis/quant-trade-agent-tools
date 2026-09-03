"""Server-owned market context collection and validation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..client import QuantTradeClient
from ..tools import build_tool_registry
from .errors import GatewayError


@dataclass(frozen=True)
class ContextSnapshot:
    symbol: str
    as_of: str
    facts: dict[str, Any]
    sources: dict[str, dict[str, Any]]
    warnings: list[str]
    derived: dict[str, Any] = field(default_factory=dict)


class ContextCollector:
    def __init__(
        self,
        *,
        client_factory: Callable[[], QuantTradeClient] = QuantTradeClient,
    ) -> None:
        self.client_factory = client_factory

    async def collect(self, symbol: str) -> ContextSnapshot:
        if symbol not in {"9984.T", "6981.T"}:
            raise GatewayError(
                code="UNSUPPORTED_SYMBOL",
                message=f"不支持的标的: {symbol}",
                status_code=422,
            )
        client = self.client_factory()
        registry = build_tool_registry(client)
        operations = {
            "quote": (registry.call, ("quote", {"symbol": symbol})),
            "kline": (
                registry.call,
                ("kline", {"symbol": symbol, "interval": "5m", "count": 100}),
            ),
            "signals": (registry.call, ("signals", {"symbol": symbol})),
            "news": (registry.call, ("news", {"count": 50})),
            "sentiment": (registry.call, ("sentiment",)),
            "trending": (registry.call, ("trending", {"symbol": symbol})),
        }
        try:
            results = await asyncio.gather(
                *(
                    asyncio.to_thread(function, *arguments)
                    for function, arguments in operations.values()
                ),
                return_exceptions=True,
            )
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

        facts: dict[str, Any] = {}
        sources: dict[str, dict[str, Any]] = {}
        warnings = ["delayed_market_data"]
        for name, result in zip(operations, results, strict=True):
            if isinstance(result, BaseException):
                sources[name] = {"ok": False, "error": type(result).__name__}
                warnings.append(f"source_unavailable:{name}")
            else:
                facts[name] = result
                sources[name] = {"ok": True}

        derived = self._derive(facts)
        missing = [
            name
            for name in ("current_price", "regime", "adx", "rsi", "news_sentiment")
            if derived.get(name) is None
        ]
        if missing:
            raise GatewayError(
                code="CONTEXT_INCOMPLETE",
                message=f"required market context is missing: {', '.join(missing)}",
                status_code=503,
                retryable=True,
            )
        return ContextSnapshot(
            symbol=symbol,
            as_of=datetime.now(UTC).isoformat(),
            facts=facts,
            sources=sources,
            warnings=warnings,
            derived=derived,
        )

    @classmethod
    def _derive(cls, facts: dict[str, Any]) -> dict[str, Any]:
        quote = cls._object(facts.get("quote"))
        trend = cls._object(facts.get("trending"))
        sentiment = cls._object(facts.get("sentiment"))
        kline = cls._object(facts.get("kline"))
        indicators = cls._object(kline.get("indicators"))
        news = cls._object(facts.get("news"))

        articles = news.get("articles")
        tweet_scores: list[float] = []
        if isinstance(articles, list):
            for article in articles:
                if not isinstance(article, dict):
                    continue
                score = article.get("sentiment_score")
                if (
                    str(article.get("source_type", "")).lower() == "twitter"
                    and cls._number(score) is not None
                ):
                    tweet_scores.append(float(score))

        return {
            "current_price": cls._number(quote.get("price")),
            "regime": trend.get("regime") if isinstance(trend.get("regime"), str) else None,
            "adx": cls._number(trend.get("adx_value")),
            "rsi": cls._last_number(indicators.get("rsi14")),
            "news_sentiment": cls._number(sentiment.get("score")),
            "tweet_sentiment": (
                sum(tweet_scores) / len(tweet_scores) if tweet_scores else None
            ),
            "tweet_count": len(tweet_scores),
        }

    @staticmethod
    def _object(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    @classmethod
    def _last_number(cls, value: Any) -> float | None:
        if not isinstance(value, list):
            return None
        for item in reversed(value):
            number = cls._number(item)
            if number is not None:
                return number
        return None
