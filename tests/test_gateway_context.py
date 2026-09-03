from __future__ import annotations

import pytest

from agent_tools.gateway.context import ContextCollector
from agent_tools.gateway.errors import GatewayError


class FakeClient:
    def __init__(self, *, fail: set[str] | None = None) -> None:
        self.fail = fail or set()
        self.closed = False

    def _result(self, name: str, value):
        if name in self.fail:
            raise TimeoutError(f"{name} timeout")
        return value

    def quote(self, symbol: str = "9984.T"):
        return self._result("quote", {"price": 15500})

    def kline(self, interval: str, count: int, *, symbol: str = "9984.T"):
        assert (interval, count) == ("5m", 100)
        return self._result(
            "kline", {"indicators": {"rsi14": [None, 57.5]}, "candles": []}
        )

    def signals(self, symbol: str = "9984.T"):
        return self._result("signals", {"signals": []})

    def news(self, count: int):
        assert count == 50
        return self._result(
            "news",
            {
                "articles": [
                    {"source_type": "twitter", "sentiment_score": 0.3},
                    {"source_type": "twitter", "sentiment_score": -0.1},
                ]
            },
        )

    def sentiment(self):
        return self._result("sentiment", {"score": 0.2, "article_count": 10})

    def trending(self, symbol: str = "9984.T"):
        return self._result("trending", {"regime": "WeakUp", "adx_value": 25.0})

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_context_collector_collects_and_derives_legacy_facts() -> None:
    client = FakeClient()
    collector = ContextCollector(client_factory=lambda: client)

    snapshot = await collector.collect("9984.T")

    assert snapshot.facts["quote"]["price"] == 15500
    assert snapshot.derived == {
        "current_price": 15500.0,
        "regime": "WeakUp",
        "adx": 25.0,
        "rsi": 57.5,
        "news_sentiment": 0.2,
        "tweet_sentiment": pytest.approx(0.1),
        "tweet_count": 2,
    }
    assert snapshot.warnings == ["delayed_market_data"]
    assert client.closed is True


@pytest.mark.asyncio
async def test_context_collector_allows_optional_news_failure() -> None:
    client = FakeClient(fail={"news"})
    collector = ContextCollector(client_factory=lambda: client)

    snapshot = await collector.collect("9984.T")

    assert "source_unavailable:news" in snapshot.warnings
    assert snapshot.derived["tweet_sentiment"] is None
    assert snapshot.derived["tweet_count"] == 0


@pytest.mark.asyncio
async def test_context_collector_rejects_missing_required_market_fact() -> None:
    collector = ContextCollector(client_factory=lambda: FakeClient(fail={"kline"}))

    with pytest.raises(GatewayError, match="required market context") as exc_info:
        await collector.collect("9984.T")

    assert exc_info.value.code == "CONTEXT_INCOMPLETE"
    assert exc_info.value.retryable is True
