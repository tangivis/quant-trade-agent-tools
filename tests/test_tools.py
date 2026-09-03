from __future__ import annotations

from agent_tools.tools import build_tool_registry


class FakeClient:
    def quote(self, symbol: str = "9984.T"):
        return {"price": 12345}

    def kline(self, interval: str, count: int, *, symbol: str = "9984.T"):
        return {"interval": interval, "count": count}

    def signals(self, symbol: str = "9984.T"):
        return {"signals": []}

    def news(self, count: int):
        return {"count": count}

    def sentiment(self):
        return {"score": 0.1}

    def trending(self, symbol: str = "9984.T"):
        return {"regime": "WeakUp"}

    def backtest(self, strategy: str, days: int, **_kwargs):
        return {"strategy": strategy, "days": days}

    def benchmark(self, strategy: str, top: int, **_kwargs):
        return {"strategy": strategy, "top": top}

    def analyze(self, payload):
        return {"signal": "HOLD", "payload": payload}


def test_registry_exposes_nine_canonical_tools() -> None:
    registry = build_tool_registry(FakeClient())

    assert registry.names() == [
        "quote",
        "kline",
        "signals",
        "news",
        "sentiment",
        "trending",
        "backtest",
        "benchmark",
        "analyze",
    ]


def test_registry_applies_defaults_and_dispatches() -> None:
    registry = build_tool_registry(FakeClient())

    assert registry.call("kline", {}) == {"interval": "5m", "count": 100}
    assert registry.call("news", {}) == {"count": 10}
    assert registry.call("backtest", {"strategy": "vwap"}) == {
        "strategy": "vwap",
        "days": 60,
    }


def test_registry_has_no_order_execution_tool() -> None:
    registry = build_tool_registry(FakeClient())

    assert all("order" not in name for name in registry.names())
    assert all("cancel" not in name for name in registry.names())
    read_only = {spec.name: spec.read_only for spec in registry.specs()}
    assert all(read_only[name] for name in [
        "quote", "kline", "signals", "news", "sentiment", "trending"
    ])
    assert not any(read_only[name] for name in ["backtest", "benchmark", "analyze"])
