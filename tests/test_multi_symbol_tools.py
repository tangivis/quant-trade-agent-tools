from __future__ import annotations

import inspect
import json
from typing import Any

import httpx
import pytest

import agent_tools.client as client_module
from agent_tools.client import QuantTradeClient
from agent_tools.tools import build_tool_registry

SYMBOLS = ["9984.T", "6981.T"]
INTERVALS = ["1m", "5m", "15m", "1h", "1d", "1wk"]
SYMBOL_SCOPED_TOOLS = [
    "quote",
    "kline",
    "signals",
    "trending",
    "backtest",
    "benchmark",
]


def response_for(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/api/backtest/benchmark":
        return httpx.Response(
            200,
            json={"results": [{"strategy_id": "rsi"}], "best_overall": None},
        )
    if request.url.path == "/api/kline":
        return httpx.Response(200, json={"candles": []})
    return httpx.Response(200, json={"ok": True})


def test_symbol_scoped_market_requests_map_exact_queries() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_for(request)

    client = QuantTradeClient(transport=httpx.MockTransport(handler))

    client.quote("6981.T")
    client.kline("15m", 20, symbol="6981.T")
    client.signals("6981.T")
    client.trending("6981.T")

    assert [(request.url.path, dict(request.url.params)) for request in requests] == [
        ("/api/quote", {"symbol": "6981.T"}),
        ("/api/kline", {"symbol": "6981.T", "interval": "15m"}),
        ("/api/signals", {"symbol": "6981.T"}),
        ("/api/trend", {"symbol": "6981.T"}),
    ]


def test_historical_backtest_maps_full_body_without_strategy_defaults() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_for(request)

    client = QuantTradeClient(transport=httpx.MockTransport(handler))
    risk_params = {"max_position_pct": 0.2, "stop_loss_pct": 0.03}

    client.backtest(
        "vwap",
        90,
        symbol="6981.T",
        interval="15m",
        initial_cash=2_500_000,
        risk_params=risk_params,
    )

    assert requests[0].url.path == "/api/backtest/historical"
    assert json.loads(requests[0].content) == {
        "symbol": "6981.T",
        "strategy": "vwap",
        "interval": "15m",
        "days": 90,
        "initial_cash": 2_500_000,
        "risk_params": risk_params,
    }
    assert not hasattr(client_module, "_STRATEGY_DEFAULTS")


def test_benchmark_maps_fields_and_preserves_expensive_policy() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_for(request)

    client = QuantTradeClient(transport=httpx.MockTransport(handler))
    risk_params = {"max_drawdown_pct": 0.15}

    result = client.benchmark(
        "rsi",
        5,
        symbol="6981.T",
        interval="1h",
        initial_cash=3_000_000,
        risk_params=risk_params,
    )

    assert json.loads(requests[0].content) == {
        "symbol": "6981.T",
        "interval": "1h",
        "initial_cash": 3_000_000,
        "risk_params": risk_params,
        "use_history": True,
    }
    assert requests[0].extensions["timeout"]["read"] == 1800.0
    assert result["results"] == [{"strategy_id": "rsi"}]


@pytest.mark.parametrize("tool_name", SYMBOL_SCOPED_TOOLS)
def test_unknown_symbol_fails_before_network(tool_name: str) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response_for(request)

    client = QuantTradeClient(transport=httpx.MockTransport(handler))
    calls = {
        "quote": lambda: client.quote("UNKNOWN"),
        "kline": lambda: client.kline("5m", 20, symbol="UNKNOWN"),
        "signals": lambda: client.signals("UNKNOWN"),
        "trending": lambda: client.trending("UNKNOWN"),
        "backtest": lambda: client.backtest("rsi", symbol="UNKNOWN"),
        "benchmark": lambda: client.benchmark("rsi", symbol="UNKNOWN"),
    }

    with pytest.raises(ValueError, match="Unsupported symbol"):
        calls[tool_name]()
    assert requests == []


@pytest.mark.parametrize("tool_name", ["kline", "backtest", "benchmark"])
@pytest.mark.parametrize("interval", ["2m", "monthly", ""])
def test_unknown_interval_fails_before_network(tool_name: str, interval: str) -> None:
    requests: list[httpx.Request] = []
    client = QuantTradeClient(
        transport=httpx.MockTransport(
            lambda request: requests.append(request) or response_for(request)
        )
    )

    calls = {
        "kline": lambda: client.kline(interval),
        "backtest": lambda: client.backtest("rsi", interval=interval),
        "benchmark": lambda: client.benchmark("rsi", interval=interval),
    }

    with pytest.raises(ValueError, match="Unsupported interval"):
        calls[tool_name]()
    assert requests == []


@pytest.mark.parametrize("tool_name", ["backtest", "benchmark"])
def test_invalid_risk_object_fails_before_network(tool_name: str) -> None:
    requests: list[httpx.Request] = []
    client = QuantTradeClient(
        transport=httpx.MockTransport(
            lambda request: requests.append(request) or response_for(request)
        )
    )
    calls = {
        "backtest": lambda: client.backtest("rsi", risk_params=[]),  # type: ignore[arg-type]
        "benchmark": lambda: client.benchmark("rsi", risk_params=[]),  # type: ignore[arg-type]
    }

    with pytest.raises(ValueError, match="risk_params must be a JSON object"):
        calls[tool_name]()
    assert requests == []


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _record(self, name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((name, kwargs))
        return {"name": name, **kwargs}

    def quote(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._record("quote", symbol=symbol)

    def kline(
        self, interval: str = "5m", count: int = 100, *, symbol: str = "9984.T"
    ) -> dict[str, Any]:
        return self._record("kline", symbol=symbol, interval=interval, count=count)

    def signals(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._record("signals", symbol=symbol)

    def news(self, count: int = 10) -> dict[str, Any]:
        return self._record("news", count=count)

    def sentiment(self) -> dict[str, Any]:
        return self._record("sentiment")

    def trending(self, symbol: str = "9984.T") -> dict[str, Any]:
        return self._record("trending", symbol=symbol)

    def backtest(self, strategy: str, days: int = 60, **kwargs: Any) -> dict[str, Any]:
        return self._record("backtest", strategy=strategy, days=days, **kwargs)

    def benchmark(self, strategy: str, top: int = 20, **kwargs: Any) -> dict[str, Any]:
        return self._record("benchmark", strategy=strategy, top=top, **kwargs)

    def analyze(
        self, *, symbol: str = "9984.T", question: str | None = None
    ) -> dict[str, Any]:
        return self._record("analyze", symbol=symbol, question=question)


def test_registry_exposes_exact_multi_symbol_schema_and_global_feeds() -> None:
    registry = build_tool_registry(RecordingClient())
    schemas = {spec.name: spec.input_schema for spec in registry.specs()}

    for tool_name in SYMBOL_SCOPED_TOOLS:
        assert schemas[tool_name]["properties"]["symbol"] == {
            "type": "string",
            "enum": SYMBOLS,
            "default": "9984.T",
        }
    for tool_name in ["kline", "backtest", "benchmark"]:
        assert schemas[tool_name]["properties"]["interval"]["enum"] == INTERVALS
    for tool_name in ["backtest", "benchmark"]:
        assert schemas[tool_name]["properties"]["initial_cash"]["type"] == "number"
        assert schemas[tool_name]["properties"]["risk_params"]["type"] == "object"
    assert "symbol" not in schemas["news"]["properties"]
    assert "symbol" not in schemas["sentiment"]["properties"]
    assert set(schemas["analyze"]["properties"]) == {"symbol", "question"}


def test_registry_dispatches_native_analysis_without_caller_facts() -> None:
    client = RecordingClient()
    registry = build_tool_registry(client)

    registry.call("analyze", {"symbol": "6981.T", "question": "说明主要风险"})

    assert client.calls == [
        ("analyze", {"symbol": "6981.T", "question": "说明主要风险"})
    ]


def test_registry_dispatches_full_backtest_arguments() -> None:
    client = RecordingClient()
    registry = build_tool_registry(client)
    risk_params = {"max_position_pct": 0.25}

    registry.call(
        "backtest",
        {
            "symbol": "6981.T",
            "strategy": "rsi",
            "interval": "1d",
            "days": 120,
            "initial_cash": 4_000_000,
            "risk_params": risk_params,
        },
    )

    assert client.calls == [
        (
            "backtest",
            {
                "symbol": "6981.T",
                "strategy": "rsi",
                "interval": "1d",
                "days": 120,
                "initial_cash": 4_000_000,
                "risk_params": risk_params,
            },
        )
    ]


def test_registry_rejects_unknown_symbol_before_client_dispatch() -> None:
    client = RecordingClient()
    registry = build_tool_registry(client)

    with pytest.raises(ValueError, match="Unsupported symbol"):
        registry.call("quote", {"symbol": "UNKNOWN"})
    assert client.calls == []


def test_registry_has_no_trading_mutation_or_product_implementation() -> None:
    registry = build_tool_registry(RecordingClient())
    names = registry.names()
    assert not any(
        forbidden in name
        for name in names
        for forbidden in ("order", "cancel", "broker", "position")
    )
    client_source = inspect.getsource(client_module)
    assert "import quant_trade" not in client_source
    assert "from quant_trade" not in client_source
    assert "_STRATEGY_DEFAULTS" not in client_source
