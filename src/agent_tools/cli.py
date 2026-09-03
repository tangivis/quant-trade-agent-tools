"""agent_tools CLI — Click-based command line interface.

Nine canonical tool subcommands share one registry with MCP. The CLI also
provides `mcp` and optional standalone `chat` entry points. This module serves:
  - `uvx quant-trade-agent-tools <subcommand>` (CLI users)
  - MCP server tool definitions (re-exports same core functions)

This package is standalone: it has NO Python dependency on quant_trade
internals. All backend access goes through HTTP to the user's quant_trade
deployment (default: http://127.0.0.1:5188).

The `analyze` subcommand calls the existing analysis pipeline via
`POST /agent/analyze` on the configured agent service. For CI/tests,
`--offline` returns a fixture response (does not call any HTTP endpoint
or import quant_trade internals).
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from . import __version__
from .agent import OpenAICompatibleAgent
from .client import SUPPORTED_INTERVALS, SUPPORTED_SYMBOLS, QuantTradeClient
from .providers import resolve_provider
from .tools import build_tool_registry


# ============================================================
# Core functions (reused by CLI subcommands and MCP server)
# ============================================================


def run_quote(symbol: str = "9984.T") -> dict[str, Any]:
    """quote — fetch current quote snapshot from quant_trade backend."""
    return _call_tool("quote", {"symbol": symbol})


def run_kline(
    interval: str,
    count: int,
    symbol: str = "9984.T",
) -> dict[str, Any]:
    """kline — fetch K-line candles."""
    return _call_tool(
        "kline",
        {"symbol": symbol, "interval": interval, "count": count},
    )


def run_signals(symbol: str = "9984.T") -> dict[str, Any]:
    """signals — current signal + regime."""
    return _call_tool("signals", {"symbol": symbol})


def run_news(count: int) -> dict[str, Any]:
    """news — recent N news items + sentiment."""
    return _call_tool("news", {"count": count})


def run_sentiment() -> dict[str, Any]:
    """sentiment — aggregated sentiment score."""
    return _call_tool("sentiment")


def run_trending(symbol: str = "9984.T") -> dict[str, Any]:
    """trending — trend direction + ADX/RSI."""
    return _call_tool("trending", {"symbol": symbol})


def run_backtest(
    strategy: str,
    days: int,
    *,
    symbol: str = "9984.T",
    interval: str = "5m",
    initial_cash: float | None = None,
    risk_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """backtest — single strategy backtest."""
    return _call_tool(
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


def run_benchmark(
    strategy: str,
    top: int,
    *,
    symbol: str = "9984.T",
    interval: str = "5m",
    initial_cash: float | None = None,
    risk_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """benchmark — parameter scan."""
    return _call_tool(
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


def run_analyze(
    *,
    symbol: str = "9984.T",
    price: float = 0.0,
    rsi: float = 50.0,
    adx: float = 20.0,
    regime: str = "NarrowRange",
    news_sentiment: float = 0.0,
    tweet_sentiment: float = 0.0,
    tweet_count: int = 0,
    offline: bool = False,
) -> dict[str, Any]:
    """analyze — 4-agent LangGraph decision via HTTP.

    offline=True  → return a fixture response (no HTTP, no LLM call)
    offline=False → POST /agent/analyze on the quant_trade backend
    """
    if offline:
        return _analyze_offline_response(
            symbol=symbol, price=price, rsi=rsi, adx=adx, regime=regime,
            news_sentiment=news_sentiment, tweet_sentiment=tweet_sentiment,
            tweet_count=tweet_count,
        )
    return _call_tool("analyze", {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "adx": adx,
        "regime": regime,
        "news_sentiment": news_sentiment,
        "tweet_sentiment": tweet_sentiment,
        "tweet_count": tweet_count,
    })


def _analyze_offline_response(
    *,
    symbol: str,
    price: float,
    rsi: float,
    adx: float,
    regime: str,
    news_sentiment: float,
    tweet_sentiment: float,
    tweet_count: int,
) -> dict[str, Any]:
    """Offline fixture response for CI/tests.

    Returns the same dict shape as a real 4-agent decision, but with
    rule-based values instead of LLM calls. This is used by:
    - `uvx quant-trade-agent-tools analyze --offline` (manual testing)
    - CI test suite (no backend needed)
    """
    avg_sentiment = (news_sentiment + tweet_sentiment) / 2
    if regime in ("StrongUp", "WeakUp") and avg_sentiment > 0.1 and rsi < 70:
        signal = "BUY"
        reason = f"up trend + positive sentiment (rsi={rsi:.0f}, adx={adx:.0f})"
    elif regime in ("StrongDown", "WeakDown") and avg_sentiment < -0.1 and rsi > 30:
        signal = "SELL"
        reason = f"down trend + negative sentiment (rsi={rsi:.0f}, adx={adx:.0f})"
    else:
        signal = "HOLD"
        reason = "no clear signal"
    return {
        "symbol": symbol,
        "signal": signal,
        "confidence": 0.5,
        "reason": f"[offline] {reason}",
        "approved": signal in ("BUY", "SELL"),
        "final_action": signal,
        "risk_notes": "offline mode — no real analysis",
        "trend_direction": "up" if regime in ("StrongUp", "WeakUp") else (
            "down" if regime in ("StrongDown", "WeakDown") else "neutral"
        ),
        "news_summary": f"news={news_sentiment:+.2f}, tweets={tweet_sentiment:+.2f}",
    }


# ============================================================
# Canonical tool dispatch
# ============================================================


def _call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    with QuantTradeClient() as client:
        return build_tool_registry(client).call(name, arguments)


# ============================================================
# Click CLI
# ============================================================


@click.group()
@click.version_option(version=__version__, prog_name="agent-tools")
def main() -> None:
    """quant_trade 的独立 CLI、MCP 与多模型 agent 入口。"""
    pass


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
def quote(symbol: str) -> None:
    """Fetch current quote snapshot."""
    _emit(run_quote(symbol))


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
@click.option("--interval", type=click.Choice(SUPPORTED_INTERVALS), default="5m", show_default=True)
@click.option("--count", default=100, type=int, help="Number of candles.")
def kline(symbol: str, interval: str, count: int) -> None:
    """Fetch K-line candles."""
    _emit(run_kline(interval=interval, count=count, symbol=symbol))


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
def signals(symbol: str) -> None:
    """Current signal + regime."""
    _emit(run_signals(symbol))


@main.command()
@click.option("--count", default=10, type=int, help="Number of news items.")
def news(count: int) -> None:
    """Recent N news items + sentiment."""
    _emit(run_news(count=count))


@main.command()
def sentiment() -> None:
    """Aggregated sentiment score."""
    _emit(run_sentiment())


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
def trending(symbol: str) -> None:
    """Trend direction + ADX/RSI/regime."""
    _emit(run_trending(symbol))


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
@click.option("--strategy", required=True, help="Strategy id (e.g. ma_cross, vwap).")
@click.option("--interval", type=click.Choice(SUPPORTED_INTERVALS), default="5m", show_default=True)
@click.option("--days", default=60, type=int, help="Lookback days.")
@click.option("--initial-cash", type=click.FloatRange(min=0, min_open=True), default=None)
@click.option("--risk-params", callback=lambda ctx, param, value: _json_object(value), default="{}")
def backtest(
    symbol: str,
    strategy: str,
    interval: str,
    days: int,
    initial_cash: float | None,
    risk_params: dict[str, Any],
) -> None:
    """Run single strategy backtest."""
    _emit(
        run_backtest(
            strategy=strategy,
            days=days,
            symbol=symbol,
            interval=interval,
            initial_cash=initial_cash,
            risk_params=risk_params,
        )
    )


@main.command()
@click.option("--symbol", type=click.Choice(SUPPORTED_SYMBOLS), default="9984.T", show_default=True)
@click.option("--strategy", required=True, help="Strategy id.")
@click.option("--interval", type=click.Choice(SUPPORTED_INTERVALS), default="5m", show_default=True)
@click.option("--top", default=20, type=int, help="Top N parameter combos.")
@click.option("--initial-cash", type=click.FloatRange(min=0, min_open=True), default=None)
@click.option("--risk-params", callback=lambda ctx, param, value: _json_object(value), default="{}")
def benchmark(
    symbol: str,
    strategy: str,
    interval: str,
    top: int,
    initial_cash: float | None,
    risk_params: dict[str, Any],
) -> None:
    """Run parameter scan benchmark."""
    _emit(
        run_benchmark(
            strategy=strategy,
            top=top,
            symbol=symbol,
            interval=interval,
            initial_cash=initial_cash,
            risk_params=risk_params,
        )
    )


@main.command()
@click.option("--symbol", default="9984.T", help="Stock symbol.")
@click.option("--price", default=0.0, type=float, help="Current price.")
@click.option("--rsi", default=50.0, type=float, help="RSI value.")
@click.option("--adx", default=20.0, type=float, help="ADX value.")
@click.option("--regime", default="NarrowRange",
              help="Market regime (NarrowRange/WeakUp/StrongUp/WeakDown/StrongDown).")
@click.option("--news-sentiment", default=0.0, type=float, help="News sentiment [-1, 1].")
@click.option("--tweet-sentiment", default=0.0, type=float, help="Tweet sentiment [-1, 1].")
@click.option("--tweet-count", default=0, type=int, help="Tweet count.")
@click.option("--offline", is_flag=True, default=False,
              help="Skip HTTP — return fixture response (CI/tests).")
def analyze(
    symbol: str,
    price: float,
    rsi: float,
    adx: float,
    regime: str,
    news_sentiment: float,
    tweet_sentiment: float,
    tweet_count: int,
    offline: bool,
) -> None:
    """4-agent LangGraph trading decision (via HTTP to quant_trade backend)."""
    result = run_analyze(
        symbol=symbol,
        price=price,
        rsi=rsi,
        adx=adx,
        regime=regime,
        news_sentiment=news_sentiment,
        tweet_sentiment=tweet_sentiment,
        tweet_count=tweet_count,
        offline=offline,
    )
    _emit(result)


@main.command("mcp")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"]),
    default="stdio",
    show_default=True,
)
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, type=int, show_default=True)
def mcp_command(transport: str, host: str, port: int) -> None:
    """Run the MCP server over stdio or Streamable HTTP."""
    from .mcp_server import run_mcp_server

    run_mcp_server(transport, host=host, port=port)


@main.command("gateway")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8010, type=click.IntRange(1, 65535), show_default=True)
def gateway_command(host: str, port: int) -> None:
    """Run the optional REST Gateway for product integration."""
    try:
        from .gateway.app import run_gateway
    except ModuleNotFoundError as exc:
        if exc.name in {"fastapi", "uvicorn"}:
            raise click.ClickException(
                "Gateway dependencies are missing; install with "
                "`uv sync --extra gateway`."
            ) from exc
        raise

    run_gateway(host=host, port=port)


@main.command("chat")
@click.argument("prompt")
@click.option(
    "--provider",
    type=click.Choice(["openai", "deepseek", "kimi", "minimax", "ollama", "custom"]),
    default=None,
    help="LLM provider preset; defaults to LLM_PROVIDER or openai.",
)
@click.option("--max-iterations", default=4, type=click.IntRange(1, 10), show_default=True)
def chat_command(prompt: str, provider: str | None, max_iterations: int) -> None:
    """Run one standalone multi-model agent turn."""
    config = resolve_provider(provider)
    with QuantTradeClient() as client:
        agent = OpenAICompatibleAgent(
            config=config,
            tools=build_tool_registry(client),
            max_iterations=max_iterations,
        )
        click.echo(agent.run(prompt))


def _emit(obj: Any) -> None:
    """Print result as JSON to stdout."""
    click.echo(json.dumps(obj, ensure_ascii=False, default=str))


def _json_object(value: str | None) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise click.BadParameter("must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise click.BadParameter("must be a JSON object")
    return parsed


if __name__ == "__main__":
    sys.exit(main())
