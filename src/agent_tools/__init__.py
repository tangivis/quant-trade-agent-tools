"""Independent CLI, MCP and model runtime for quant_trade.

This package is a standalone extraction from the quant_trade monorepo.
It has NO Python dependency on quant_trade internals. All backend
access goes through HTTP to the user's quant_trade deployment
(default: http://127.0.0.1:5188).

The `analyze` subcommand calls the native Gateway configured by
`QUANT_TRADE_GATEWAY_URL`. The optional standalone runtime uses any
OpenAI-compatible model endpoint without coupling it to a harness.
"""

__version__ = "0.4.0"

__all__ = ["__version__"]
