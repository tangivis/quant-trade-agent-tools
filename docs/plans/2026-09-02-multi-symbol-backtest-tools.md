# Multi-symbol Backtest Tools — Implementation Plan

## Scope

Modify only `quant-trade-agent-tools` on `feature/multi-symbol-backtest-tools`. Preserve the independent
release-runbook branch. Do not modify the sibling product repository, merge, tag or deploy.

## Red -> Green -> Refactor

1. Freeze the two supported symbols, six intervals and six symbol-scoped tool list in tests.
2. Write exact `httpx.MockTransport` request tests before changing `QuantTradeClient`.
3. Write ToolRegistry dispatch/schema tests, including unknown-symbol failure before fake-client calls.
4. Write real MCP `tools/list` and `tools/call` tests for the second symbol and enum parity.
5. Write TypeScript red tests for shared schemas, object CLI serialization and pi/dsh registered
   parameters.
6. Record the focused failures, then implement the smallest client and schema changes.
7. Refactor repeated enum validation into transport-level helpers; keep domain logic out.
8. Update public descriptions so market/backtest tools are dual-symbol and news/sentiment are global.
9. Run focused/full Python, Bun tests, typecheck, builds, artifact inspection and secret/boundary scans.
10. Commit implementation and documentation in dependency-safe conventional slices, pushing each
    immediately; create an MR to `main` without merging it.
11. Add explicit `0.3.0` Python/TypeScript version tests, then propagate one version through manifests,
    locks, runtime discovery and release documentation.
12. Keep MR `!4` Draft after the version commit. Wait for explicit product deployment confirmation
    before any real loopback call.
13. After confirmation, run only bounded quote/kline and historical backtest smoke for `6981.T`; record
    redacted shape/latency evidence, push it, and only then mark the MR ready.

## Commit plan

1. `feat(tools): add multi-symbol market and backtest contracts` — client, Python registry/CLI/MCP,
   Python tests, OpenSpec/plan and initial changelog.
2. `feat(adapters): align harness schemas for multi-symbol backtests` — TypeScript bridge, pi/dsh parity
   tests and adapter documentation.
3. `docs: publish dual-symbol tool boundaries` — public architecture, README, detailed functions,
   release/handoff verification and final audit evidence.

Adjacent slices may be combined only if separating them produces a failing committed tree.

## Rollout and rollback

Product `v1.5.62` deployed the backward-compatible untagged string-ID input while retaining full config
support and Rust-only default resolution. Smoke exposed product optimizer starvation; product MR `!154`
contains the fix, and product `v1.5.63` passed stability checks with the optimizer active. Rollback
restores the prior adapter version; no product data or strategy migration is involved. Benchmark remains
opt-in/expensive and dsh remains experimental.

## Evidence

- Python red: 19 failed / 3 passed. Failures covered missing symbol/interval arguments, exact HTTP body,
  local fail-closed validation, registry/MCP schemas, CLI options and the copied strategy-default map.
- TypeScript red: 18 passed / 2 failed / 1 module error. The bridge lacked exported enums and serialized
  `risk_params` as `[object Object]`; pi/dsh shared-snapshot assertions already passed.
- Focused Python green/refactor: 48 passed. This includes exact requests, CLI, registry, real MCP call,
  existing tool/runtime/context compatibility and local no-network rejection.
- Focused TypeScript green/refactor: 29 passed / 0 failed / 135 assertions. One initial combined run
  hit the existing dsh cancellation wall-clock threshold under parallel load; its isolated and immediate
  combined reruns passed without changing the assertion.
- Full Python: 230 passed / 1 opt-in live-provider smoke skipped. Bun: 38 passed / 152 assertions.
- Typecheck, both harness builds and Python sdist/wheel build passed. Artifact/publication/boundary audit
  found no runtime secret, workstation path, local strategy defaults, sibling import or mutation tool;
  npm dry-runs retain four-file pi/dsh allowlists.
- Dependency-safe feature and documentation commits were pushed immediately. Draft MR `!4` targets
  protected `main`; its branch and merge-request pipelines passed, it has no conflicts, and it remains
  unmerged pending the product producer prerequisite.
- Version red: Python 2 failed / 6 passed; TypeScript 1 failed because synchronized metadata remained
  stale at `0.2.0`.
- Version green: focused Python 9 passed and TypeScript 1 passed; full Python 230 passed / 1 opt-in live
  smoke skipped, Bun 39 passed / 153 assertions, typecheck/build passed.
- `0.3.0` sdist/wheel contain 46/23 files; pi/dsh dry-runs remain four files each at `0.3.0`; CLI and
  wheel metadata report `0.3.0`; secret/local-path/strategy-copy/import audits passed.
- Production attempt 1: direct quote timed out at the read boundary while the `v1.5.62` CPU-bound
  optimizer starved the product runtime; four short quote probes also timed out. No later tool ran.
- Production attempt 2 after restart: direct quote/kline/string-ID historical succeeded; MCP quote
  succeeded, then kline encountered timeout/reset during a second producer starvation window. After the
  operator restart, MCP kline retry and historical succeeded. The full script exited successfully.
- Clean MCP-only retry: quote 1468ms, 15m kline 32ms (8 candles), string-ID historical 629ms; schema and
  no-trading-mutation checks passed. No payload bodies were recorded.
- Product `v1.5.63` readiness: optimizer hotfix deployed; product-owned checks ran after the optimizer
  was active, with repeated health and `6981.T` quote requests all HTTP 200, correct symbol identity and
  bounded low-millisecond latency. Exact environment metrics and raw logs are not stored here.
- Final action: push this sanitized evidence, wait for its MR pipeline success, then mark MR `!4` ready
  without merge, tag or deploy.
