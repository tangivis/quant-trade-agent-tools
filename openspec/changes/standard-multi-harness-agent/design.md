# Design: Standard Multi-Harness Agent

## Architecture

```text
pi / dsh / Codex / Claude / Cursor / custom host
                         |
                 MCP stdio or HTTP
                         |
              quant-trade-agent-tools
              +-----------------------+
              | MCP server            |
              | canonical tool registry|
              | optional agent loop   |
              | model provider factory|
              | QuantTradeClient      |
              +-----------+-----------+
                          |
                    HTTP API v1
                          |
                    quant_trade
```

## Boundaries

`quant_trade` remains the provider of truth for market data, indicators,
signals, sentiment, backtests and its four-agent decision pipeline. This repo
must not import `quant_trade` modules or connect to its database.

Harnesses normally own the LLM. They call this project through MCP or a native
adapter, so model selection is entirely a harness concern. The standalone
`chat` command is optional and uses an OpenAI-compatible HTTP contract.

## Canonical Tools

The first release preserves the nine public names for compatibility:

`quote`, `kline`, `signals`, `news`, `sentiment`, `trending`, `backtest`,
`benchmark`, `analyze`.

Tool definitions live once in Python. The MCP server registers those functions
directly. TypeScript keeps a generated-compatible schema snapshot guarded by
tests until schema generation is added.

## Upstream API Normalization

The public tool contract is intentionally simpler than the current upstream
HTTP shapes. `QuantTradeClient` owns all normalization:

- `news` wraps the upstream JSON array as `{ "articles": [...] }` so every
  tool returns an object.
- `kline.count` is applied locally because `/api/kline` accepts `interval` but
  not `count`.
- `backtest.strategy` is expanded to a valid tagged `StrategyConfig` with
  documented defaults and sent to `/api/backtest/historical` together with
  `days` and a fixed `5m` interval.
- `benchmark` sends the upstream-supported interval/history request, then
  filters by `strategy` and limits the returned result list to `top`.
- benchmark calls use a 30-minute HTTP and adapter timeout because the upstream
  grid search is intentionally compute-heavy.

This translation belongs in the client boundary. Harness adapters must not
know the Rust request structures.

## Model Providers

All standalone providers use the same chat-completions-style JSON contract.
Presets supply a default base URL and model environment variable; every value
can be overridden:

- `openai`
- `deepseek`
- `kimi`
- `minimax`
- `ollama`
- `custom`

Secrets are read only from environment variables. They are never accepted as
CLI arguments or written to config files.

## Safety

- Read-only tools are annotated as read-only in MCP.
- Backtest, benchmark and analyze are compute tools, not execution tools.
- No order tool is exposed.
- API bearer tokens are optional for loopback development and supported for
  remote deployments.
- Tool output includes backend errors; the model never receives fabricated
  live data as a successful result.

## Compatibility

- MCP is the primary compatibility surface.
- pi is a native UX adapter over the same CLI contract.
- dsh is an experimental native adapter; MCP should be preferred if/when dsh
  provides a stable MCP client surface.
