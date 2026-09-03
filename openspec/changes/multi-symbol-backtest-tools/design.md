# Design: Multi-symbol Backtest Tools

## Ownership boundary

`quant_trade` remains the Product/Data/Domain Plane and owns market facts, strategies, risk parameters,
backtest execution and persistence. This repository remains the Intelligence Plane adapter: it validates
the published enum boundary, maps arguments to HTTP, and exposes stable CLI/MCP/harness schemas.

The client must not contain strategy defaults or reconstruct Rust `StrategyConfig`. Strategy names and
request field enums are transport-contract metadata, not trading implementations. Historical requests
send an untagged string strategy ID; only Rust `StrategyConfig::default_for_id` may attach defaults.

## Canonical contract

```text
symbols   = 9984.T | 6981.T
intervals = 1m | 5m | 15m | 1h | 1d | 1wk
```

| Tool | Product request | Symbol-scoped |
|---|---|---|
| quote | `GET /api/quote?symbol=...` | yes |
| kline | `GET /api/kline?symbol=...&interval=...` | yes |
| signals | `GET /api/signals?symbol=...` | yes |
| trending | `GET /api/trend?symbol=...` | yes |
| backtest | `POST /api/backtest/historical` | yes |
| benchmark | `POST /api/backtest/benchmark` | yes |
| news | `GET /api/intel/news` | no; global feed |
| sentiment | `GET /api/intel/sentiment` | no; global aggregate |

Backtest body fields are `symbol`, caller-supplied `strategy`, `interval`, `days`, `risk_params`, plus
`initial_cash` only when provided. Benchmark keeps the existing expensive timeout, result filtering and
`use_history` behavior while forwarding `symbol`, `interval`, `risk_params`, and optional
`initial_cash`.

## Validation and failure behavior

- `QuantTradeClient` validates symbols and intervals before constructing a request.
- ToolRegistry handlers repeat enum validation so standalone agents fail before reaching even a fake or
  alternate client.
- CLI uses bounded choices and parses `risk_params` only as a JSON object.
- TypeScript serializes object arguments as JSON rather than JavaScript string coercion.
- Invalid enums or non-object risk parameters raise local validation errors; no fallback symbol is used.

## Interface parity

Python ToolRegistry is the semantic source of truth. MCP typed functions expose matching enum fields;
the TypeScript bridge snapshot mirrors the same fields/defaults. pi and dsh continue importing that
single TypeScript snapshot and do not implement domain logic.

News and sentiment intentionally omit `symbol`. Their descriptions say global upstream feed so callers
cannot infer per-symbol isolation.

## Compatibility and rollout

Defaults preserve existing `9984.T`, `5m`, 60-day behavior. Product MR `quant_trade!152` has added
string-ID or full-config compatibility to product `main` without moving default resolution out of Rust.
Product `v1.5.62` deployed this contract; product `v1.5.63` deployed the optimizer starvation fix and
passed stability checks with the optimizer active.

Rollback reverts only adapter fields and schemas. It never changes or migrates product backtest data.

Product `v1.5.62` deployment enabled the production client/MCP smoke. The first attempt timed out before
tool progression because the product optimizer starved Tokio. After restarts, direct client completed;
MCP experienced timeout/reset during a second starvation window, then completed after retry. A separate
clean MCP-only run completed continuously. These are producer runtime events, not adapter failures.

Product-owned post-hotfix acceptance repeatedly exercised health and second-symbol quote while the
optimizer was active; every request succeeded with low-millisecond bounded latency and correct symbol
identity. Combined with the earlier client/MCP contract smoke, this satisfies the readiness gate. MR
`!4` may become ready only after the final documentation pipeline succeeds.

## Version propagation

`0.3.0` is a single release identity propagated through `pyproject.toml`, Python `__version__`, the uv
lock, root/bridge/pi/dsh package manifests and Bun workspace lock. Gateway `/health` and authenticated
`/v1/capabilities` derive their version from Python `__version__`; MCP derives from the same source.
Contract version remains `v1` and dsh remains experimental. Version tests use an explicit expected
release value so synchronized-but-stale `0.2.0` metadata cannot pass.
