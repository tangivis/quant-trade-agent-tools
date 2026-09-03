from __future__ import annotations

import pytest

import agent_tools.mcp_server as mcp_server
from agent_tools.mcp_server import create_mcp_server


SYMBOLS = ["9984.T", "6981.T"]
INTERVALS = ["1m", "5m", "15m", "1h", "1d", "1wk"]


class FakeClient:
    def quote(self, symbol: str = "9984.T"):
        return {"price": 15500, "symbol": symbol}

    def kline(self, interval: str, count: int, *, symbol: str = "9984.T"):
        return {"interval": interval, "count": count}

    def signals(self, symbol: str = "9984.T"):
        return {"signals": []}

    def news(self, count: int):
        return {"count": count}

    def sentiment(self):
        return {"score": 0}

    def trending(self, symbol: str = "9984.T"):
        return {"regime": "NarrowRange"}

    def backtest(self, strategy: str, days: int, **_kwargs):
        return {"strategy": strategy, "days": days}

    def benchmark(self, strategy: str, top: int, **_kwargs):
        return {"strategy": strategy, "top": top}

    def analyze(self, payload):
        return {"signal": "HOLD", "payload": payload}


def test_mcp_server_reports_the_package_version(monkeypatch) -> None:
    monkeypatch.setattr(mcp_server, "__version__", "9.9.9", raising=False)

    assert create_mcp_server(FakeClient()).version == "9.9.9"


@pytest.mark.asyncio
async def test_mcp_server_lists_and_calls_tools() -> None:
    from mcp import Client

    server = create_mcp_server(FakeClient())
    async with Client(server) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools.tools]
        assert names == [
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
        assert all(tool.annotations is not None for tool in tools.tools)
        assert all(tool.annotations.destructive_hint is False for tool in tools.tools)
        annotations = {tool.name: tool.annotations for tool in tools.tools}
        assert annotations["quote"].read_only_hint is True
        assert annotations["backtest"].read_only_hint is False
        assert annotations["benchmark"].read_only_hint is False
        assert annotations["analyze"].read_only_hint is False

        result = await client.call_tool("quote", {})
        assert result.structured_content == {"price": 15500, "symbol": "9984.T"}


@pytest.mark.asyncio
async def test_mcp_multi_symbol_schema_matches_canonical_contract() -> None:
    from mcp import Client

    server = create_mcp_server(FakeClient())
    async with Client(server) as client:
        listed = await client.list_tools()
        schemas = {tool.name: tool.input_schema for tool in listed.tools}

        for tool_name in [
            "quote",
            "kline",
            "signals",
            "trending",
            "backtest",
            "benchmark",
        ]:
            assert schemas[tool_name]["properties"]["symbol"]["enum"] == SYMBOLS
        for tool_name in ["kline", "backtest", "benchmark"]:
            assert schemas[tool_name]["properties"]["interval"]["enum"] == INTERVALS
        assert "symbol" not in schemas["news"]["properties"]
        assert "symbol" not in schemas["sentiment"]["properties"]

        result = await client.call_tool("quote", {"symbol": "6981.T"})
        assert result.structured_content == {"price": 15500, "symbol": "6981.T"}
