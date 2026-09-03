# Specification: Multi-symbol Backtest Tools

## Requirement: supported symbols fail closed

The six symbol-scoped tools MUST accept only `9984.T` and `6981.T`. Unknown symbols MUST raise locally
before an HTTP transport or tool handler is invoked.

### Scenario: second symbol quote

Given `symbol=6981.T`, quote sends exactly that symbol as the product query and returns the product
object unchanged.

### Scenario: unknown symbol

Given any other symbol, quote, kline, signals, trending, backtest and benchmark fail without network
activity.

## Requirement: backtest request is an adapter mapping

Historical backtest MUST POST caller-supplied `symbol`, `strategy`, `interval`, `days` and
`risk_params`. It MUST include `initial_cash` when supplied and MUST NOT synthesize strategy parameters.
`strategy` MUST be the untagged string ID supplied by the caller. Product `v1.5.62` deployed the
compatible producer from MR `quant_trade!152`; the successful HTTP 200 backtest smoke confirms the
string-ID contract without any adapter-side default expansion.

### Scenario: full historical request

A request for `6981.T`, a supported strategy, `15m`, a lookback, cash and risk object reaches
`/api/backtest/historical` with equal JSON values.

### Scenario: product resolves the ID

After the producer dependency is deployed, Rust accepts either the untagged ID or an existing full
config, applies defaults only through `StrategyConfig::default_for_id`, and rejects an unknown ID. The
Intelligence Plane never performs that resolution.

## Requirement: benchmark preserves expensive-tool policy

Benchmark MUST POST symbol, interval, risk parameters and optional initial cash to
`/api/backtest/benchmark`, retain its long timeout and local top/strategy filtering, and remain a
non-read-only, non-destructive tool.

## Requirement: global intelligence feeds are honest

News and sentiment MUST NOT accept or forward a symbol while their product endpoints are global. Public
descriptions MUST identify this limitation.

## Requirement: every thin adapter exposes one schema

ToolRegistry, real MCP, CLI bridge, pi and dsh MUST expose matching symbol and interval enums for all six
symbol-scoped tools. Risk objects MUST survive CLI serialization as JSON objects.

## Requirement: no trading mutation

The canonical registry MUST contain no order, cancel, broker, position-mutation or live-execution tool.
This repository MUST NOT import product internals, access its database or copy its backtest engine.

## Requirement: one 0.3.0 release identity

Python package/runtime, root TypeScript workspace, CLI bridge, pi, dsh and their workspace lock metadata
MUST all report `0.3.0`. Gateway health/capabilities and MCP MUST expose the same runtime version while
the HTTP contract version remains `v1`.

### Scenario: synchronized but stale versions

If every manifest still says `0.2.0`, the explicit release-version tests fail even though the manifests
agree with each other.

### Scenario: capabilities discovery

An authenticated capabilities request returns `version=0.3.0` without changing the supported Gateway
analysis symbol or falsely advertising a second-symbol native analyze contract.

## Requirement: staged production smoke is gated

Real smoke is limited to read-only quote/kline plus a historical backtest for `6981.T`, strategy `rsi`,
interval `15m` and a five-day lookback; it MUST NOT call any order, cancel, broker or live-execution
endpoint. Timeout/reset caused by producer runtime starvation MUST be recorded as an explicit failed
attempt rather than blamed on the adapter or converted into success.

Product `v1.5.62` smoke establishes the HTTP/MCP contracts. Product `v1.5.63` MUST deploy the optimizer
isolation fix, and product-owned checks MUST show stable health and second-symbol quote responses while
the optimizer is active before the Agent MR becomes ready.

### Scenario: post-hotfix readiness

Given deployed product `v1.5.63`, repeated health and `6981.T` quote checks all return HTTP 200 with
bounded low-millisecond latency while the optimizer is active. The result is recorded without price,
host, commit, pipeline or raw log details, and the Agent MR may be marked ready after its evidence
pipeline succeeds.
