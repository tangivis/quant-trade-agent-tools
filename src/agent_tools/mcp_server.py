"""Real MCP v2 server exposing the canonical quant_trade tools."""

from __future__ import annotations

from typing import Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from . import __version__
from .client import QuantTradeClient, SupportedInterval, SupportedSymbol
from .tools import TOOL_NAMES, ToolRegistry, build_tool_registry

READ_ONLY_TOOL = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)

COMPUTE_TOOL = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=True,
)


def create_mcp_server(client: QuantTradeClient | None = None) -> MCPServer:
    registry = build_tool_registry(client or QuantTradeClient())
    server = MCPServer(
        "quant-trade-agent-tools",
        title="Quant Trade Agent Tools",
        description=(
            "9984.T and 6981.T market data, signals, backtests and decision support; "
            "news/sentiment feeds are global."
        ),
        instructions=(
            "Use tools for all live values. Results are delayed market data and "
            "decision support, not broker execution or financial guarantees."
        ),
        version=__version__,
    )
    _register_tools(server, registry)
    return server


def _register_tools(server: MCPServer, registry: ToolRegistry) -> None:
    @server.tool(name="quote", structured_output=True, annotations=READ_ONLY_TOOL)
    def quote(symbol: SupportedSymbol = "9984.T") -> dict[str, object]:
        """Get the latest 9984.T or 6981.T quote snapshot in JPY."""
        return registry.call("quote", {"symbol": symbol})

    @server.tool(name="kline", structured_output=True, annotations=READ_ONLY_TOOL)
    def kline(
        symbol: SupportedSymbol = "9984.T",
        interval: SupportedInterval = "5m",
        count: int = 100,
    ) -> dict[str, object]:
        """Get 9984.T or 6981.T candlesticks for technical analysis."""
        return registry.call(
            "kline",
            {"symbol": symbol, "interval": interval, "count": count},
        )

    @server.tool(name="signals", structured_output=True, annotations=READ_ONLY_TOOL)
    def signals(symbol: SupportedSymbol = "9984.T") -> dict[str, object]:
        """Get current quant_trade signals and market regime for either supported symbol."""
        return registry.call("signals", {"symbol": symbol})

    @server.tool(name="news", structured_output=True, annotations=READ_ONLY_TOOL)
    def news(count: int = 10) -> dict[str, object]:
        """Get the global upstream news feed; results are not symbol-isolated."""
        return registry.call("news", {"count": count})

    @server.tool(name="sentiment", structured_output=True, annotations=READ_ONLY_TOOL)
    def sentiment() -> dict[str, object]:
        """Get global aggregate sentiment; results are not symbol-isolated."""
        return registry.call("sentiment")

    @server.tool(name="trending", structured_output=True, annotations=READ_ONLY_TOOL)
    def trending(symbol: SupportedSymbol = "9984.T") -> dict[str, object]:
        """Get trend regime, ADX, directional indicators and RSI for either symbol."""
        return registry.call("trending", {"symbol": symbol})

    @server.tool(name="backtest", structured_output=True, annotations=COMPUTE_TOOL)
    def backtest(
        strategy: str,
        symbol: SupportedSymbol = "9984.T",
        interval: SupportedInterval = "5m",
        days: int = 60,
        initial_cash: float | None = None,
        risk_params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Run a historical strategy backtest without placing orders."""
        return registry.call(
            "backtest",
            {
                "symbol": symbol,
                "strategy": strategy,
                "interval": interval,
                "days": days,
                "initial_cash": initial_cash,
                "risk_params": risk_params or {},
            },
        )

    @server.tool(name="benchmark", structured_output=True, annotations=COMPUTE_TOOL)
    def benchmark(
        strategy: str,
        symbol: SupportedSymbol = "9984.T",
        interval: SupportedInterval = "5m",
        top: int = 20,
        initial_cash: float | None = None,
        risk_params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Scan strategy parameters without placing orders."""
        return registry.call(
            "benchmark",
            {
                "symbol": symbol,
                "strategy": strategy,
                "interval": interval,
                "top": top,
                "initial_cash": initial_cash,
                "risk_params": risk_params or {},
            },
        )

    @server.tool(name="analyze", structured_output=True, annotations=COMPUTE_TOOL)
    def analyze(
        symbol: SupportedSymbol = "9984.T",
        question: str | None = None,
    ) -> dict[str, object]:
        """Run native analysis from server-collected facts; this never places an order."""
        return registry.call(
            "analyze",
            {
                "symbol": symbol,
                "question": question,
            },
        )

    @server.tool(name="conversation_create", structured_output=True, annotations=COMPUTE_TOOL)
    def conversation_create(
        channel: Literal["chat", "wish"] = "chat",
        symbol: SupportedSymbol = "9984.T",
        title: str | None = None,
    ) -> dict[str, object]:
        """Create a product-owned thread shared across supported Harness clients."""
        return registry.call(
            "conversation_create",
            {"channel": channel, "symbol": symbol, "title": title},
        )

    @server.tool(name="conversation_context", structured_output=True, annotations=READ_ONLY_TOOL)
    def conversation_context(thread_id: str) -> dict[str, object]:
        """Read one product-owned conversation summary and recent messages."""
        return registry.call("conversation_context", {"thread_id": thread_id})

    @server.tool(name="conversation_append", structured_output=True, annotations=COMPUTE_TOOL)
    def conversation_append(
        thread_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> dict[str, object]:
        """Append one message to a product-owned conversation thread."""
        return registry.call(
            "conversation_append",
            {"thread_id": thread_id, "role": role, "content": content},
        )


def run_mcp_server(
    transport: Literal["stdio", "streamable-http"] = "stdio",
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    server = create_mcp_server()
    if transport == "stdio":
        server.run()
    else:
        server.run(transport="streamable-http", host=host, port=port)


def list_tools() -> list[str]:
    return list(TOOL_NAMES)
