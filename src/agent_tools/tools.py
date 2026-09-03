"""Canonical agent tool definitions shared by CLI, MCP and model runtime."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .client import (
    BENCHMARK_STRATEGIES,
    SUPPORTED_INTERVALS,
    SUPPORTED_STRATEGIES,
    SUPPORTED_SYMBOLS,
    QuantTradeClient,
    require_initial_cash,
    require_risk_params,
    require_supported_interval,
    require_supported_symbol,
)

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]

TOOL_NAMES = (
    "quote",
    "kline",
    "signals",
    "news",
    "sentiment",
    "trending",
    "backtest",
    "benchmark",
    "analyze",
    "conversation_create",
    "conversation_context",
    "conversation_append",
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    read_only: bool = True

    def openai_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolRegistry:
    def __init__(self, specs: list[ToolSpec]) -> None:
        self._specs = {spec.name: spec for spec in specs}

    def names(self) -> list[str]:
        return list(self._specs)

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def without(self, names: set[str]) -> ToolRegistry:
        return ToolRegistry(
            [spec for spec in self._specs.values() if spec.name not in names]
        )

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            spec = self._specs[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name}") from exc
        return spec.handler(arguments or {})


def _object_schema(
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


def _symbol(arguments: dict[str, Any]) -> str:
    return require_supported_symbol(arguments.get("symbol", "9984.T"))


def _interval(arguments: dict[str, Any]) -> str:
    return require_supported_interval(arguments.get("interval", "5m"))


def _initial_cash(arguments: dict[str, Any]) -> float | None:
    value = arguments.get("initial_cash")
    return None if value is None else require_initial_cash(value)


def _risk_params(arguments: dict[str, Any]) -> dict[str, Any]:
    return require_risk_params(arguments.get("risk_params"))


def _symbol_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "enum": list(SUPPORTED_SYMBOLS),
        "default": "9984.T",
    }


def _interval_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "enum": list(SUPPORTED_INTERVALS),
        "default": "5m",
    }


def build_tool_registry(client: QuantTradeClient) -> ToolRegistry:
    specs = [
        ToolSpec(
            "quote",
            "Get the latest 9984.T or 6981.T quote snapshot in JPY.",
            _object_schema({"symbol": _symbol_schema()}),
            lambda args: client.quote(_symbol(args)),
        ),
        ToolSpec(
            "kline",
            "Get 9984.T or 6981.T candlesticks for technical analysis.",
            _object_schema(
                {
                    "symbol": _symbol_schema(),
                    "interval": _interval_schema(),
                    "count": {"type": "integer", "minimum": 1, "maximum": 400, "default": 100},
                }
            ),
            lambda args: client.kline(
                _interval(args),
                args.get("count", 100),
                symbol=_symbol(args),
            ),
        ),
        ToolSpec(
            "signals",
            "Get current quant_trade trading signals for 9984.T or 6981.T.",
            _object_schema({"symbol": _symbol_schema()}),
            lambda args: client.signals(_symbol(args)),
        ),
        ToolSpec(
            "news",
            "Get the global upstream news feed; results are not symbol-isolated.",
            _object_schema({"count": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10}}),
            lambda args: client.news(args.get("count", 10)),
        ),
        ToolSpec(
            "sentiment",
            "Get global aggregated sentiment in [-1, 1]; it is not symbol-isolated.",
            _object_schema(),
            lambda _args: client.sentiment(),
        ),
        ToolSpec(
            "trending",
            "Get trend regime, ADX, directional indicators and RSI for 9984.T or 6981.T.",
            _object_schema({"symbol": _symbol_schema()}),
            lambda args: client.trending(_symbol(args)),
        ),
        ToolSpec(
            "backtest",
            "Run a historical strategy backtest. This is compute-heavy but does not place orders.",
            _object_schema(
                {
                    "symbol": _symbol_schema(),
                    "strategy": {"type": "string", "enum": list(SUPPORTED_STRATEGIES)},
                    "interval": _interval_schema(),
                    "days": {"type": "integer", "minimum": 1, "default": 60},
                    "initial_cash": {"type": "number", "exclusiveMinimum": 0},
                    "risk_params": {"type": "object", "default": {}},
                },
                ["strategy"],
            ),
            lambda args: client.backtest(
                args["strategy"],
                args.get("days", 60),
                symbol=_symbol(args),
                interval=_interval(args),
                initial_cash=_initial_cash(args),
                risk_params=_risk_params(args),
            ),
            read_only=False,
        ),
        ToolSpec(
            "benchmark",
            "Scan strategy parameters. This is compute-heavy but does not place orders.",
            _object_schema(
                {
                    "symbol": _symbol_schema(),
                    "strategy": {"type": "string", "enum": list(BENCHMARK_STRATEGIES)},
                    "interval": _interval_schema(),
                    "top": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "initial_cash": {"type": "number", "exclusiveMinimum": 0},
                    "risk_params": {"type": "object", "default": {}},
                },
                ["strategy"],
            ),
            lambda args: client.benchmark(
                args["strategy"],
                args.get("top", 20),
                symbol=_symbol(args),
                interval=_interval(args),
                initial_cash=_initial_cash(args),
                risk_params=_risk_params(args),
            ),
            read_only=False,
        ),
        ToolSpec(
            "analyze",
            "Run native Gateway analysis from server-collected facts. Returns advice, never places an order.",
            _object_schema(
                {
                    "symbol": _symbol_schema(),
                    "question": {"type": "string", "minLength": 1, "maxLength": 2000},
                }
            ),
            lambda args: client.analyze(
                symbol=_symbol(args), question=args.get("question")
            ),
            read_only=False,
        ),
        ToolSpec(
            "conversation_create",
            "Create a product-owned conversation thread for shared Harness context.",
            _object_schema(
                {
                    "channel": {"type": "string", "enum": ["chat", "wish"], "default": "chat"},
                    "symbol": _symbol_schema(),
                    "title": {"type": "string", "minLength": 1, "maxLength": 200},
                }
            ),
            lambda args: client.conversation_create(
                channel=args.get("channel", "chat"),
                symbol=_symbol(args),
                title=args.get("title"),
            ),
            read_only=False,
        ),
        ToolSpec(
            "conversation_context",
            "Read a product-owned conversation summary and recent messages.",
            _object_schema(
                {"thread_id": {"type": "string", "minLength": 1, "maxLength": 128}},
                ["thread_id"],
            ),
            lambda args: client.conversation_context(args["thread_id"]),
        ),
        ToolSpec(
            "conversation_append",
            "Append a user or assistant message to a product-owned conversation thread.",
            _object_schema(
                {
                    "thread_id": {"type": "string", "minLength": 1, "maxLength": 128},
                    "role": {"type": "string", "enum": ["user", "assistant"]},
                    "content": {"type": "string", "minLength": 1, "maxLength": 8000},
                },
                ["thread_id", "role", "content"],
            ),
            lambda args: client.conversation_append(
                args["thread_id"], role=args["role"], content=args["content"]
            ),
            read_only=False,
        ),
    ]
    return ToolRegistry(specs)
