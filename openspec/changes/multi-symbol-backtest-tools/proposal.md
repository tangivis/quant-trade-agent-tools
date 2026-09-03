# Proposal: Multi-symbol Backtest Tools

## Problem

The canonical market and backtest tools currently assume one symbol and construct part of the
historical-backtest strategy payload locally. The Product/Data/Domain Plane now publishes a two-symbol
HTTP contract for deterministic market data and backtests. The Intelligence Plane needs to expose that
contract consistently through Python, CLI, MCP, pi and dsh without copying product strategy or engine
logic.

## Scope

- Support `9984.T` and `6981.T` for quote, kline, signals, trending, backtest and benchmark.
- Reject unknown symbols locally before any HTTP request.
- Pass the supported backtest and benchmark fields to the published product HTTP APIs without deriving
  strategy parameters in this repository.
- Keep news and sentiment explicitly global while their producer APIs are not symbol-scoped.
- Keep Python ToolRegistry, CLI, MCP and TypeScript harness schemas aligned.
- Update public capability documentation and release evidence.

## Non-goals

- No Rust strategy, indicator, risk, backtest engine or persistence implementation is copied here.
- No change to the product repository or its producer branch.
- No order, cancel, broker, position or live-execution tool.
- No claim that global news or sentiment is isolated by symbol.
- No expansion of Gateway analysis to a second symbol without its own producer contract.

## Acceptance

- Exact request tests prove symbol-aware query/body mapping for the six tools.
- `strategy`, `interval`, `days`, optional `initial_cash` and `risk_params` cross the HTTP boundary as
  caller-supplied contract data.
- Supported intervals are exactly `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`.
- ToolRegistry, MCP and TypeScript schemas expose the same symbol/interval fields and enums.
- pi and dsh register the shared schemas without local copies.
- Unknown symbols fail closed without network access, and mutation-boundary tests remain green.
- Full Python, TypeScript, typecheck, build, artifact and publication gates pass.

## Producer dependency

Product MR `quant_trade!152` has landed and the compatible producer was deployed in product `v1.5.62`.
Bounded smoke exposed a separate CPU-bound optimizer starving the product HTTP runtime; product MR
`!154` contains the fix. Product `v1.5.63` is now deployed and product-owned stability checks passed
while the optimizer was active. This repository MUST keep sending the string ID and MUST NOT restore
local default parameters. The producer/runtime readiness gate is satisfied.

## Release candidate

The additive dual-symbol/backtest contract is the `0.3.0` release boundary. Python metadata/runtime,
all TypeScript package manifests and lockfile workspace versions, health/capabilities, MCP metadata and
public release documentation must report the same version. No tag, publication or deployment is part of
this change.
