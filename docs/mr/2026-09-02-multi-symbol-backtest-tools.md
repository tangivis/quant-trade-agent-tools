<!-- visibility: internal-only; sanitized -->

# MR: Multi-symbol Backtest Tools

## Metadata

- Target: `main`
- Source: `feature/multi-symbol-backtest-tools`
- Title: `feat(tools): add dual-symbol market and backtest contracts`
- Release candidate: `0.3.0`
- Status: readiness gates satisfied; mark MR `!4` ready after this evidence pipeline succeeds

## Summary

- Add `9984.T|6981.T` to quote, kline, signals, trending, backtest and benchmark across Python,
  canonical registry, real MCP, CLI bridge, pi and experimental dsh.
- Add the exact interval enum `1m|5m|15m|1h|1d|1wk`, fail closed before network and keep global
  news/sentiment free of a misleading symbol field.
- Forward backtest/benchmark fields through the published HTTP boundary without copying product strategy,
  risk or engine logic. No order/cancel/broker tools are introduced.

## Producer-first dependency

Product MR `quant_trade!152` is merged into product `main` and accepts either the string ID deliberately
sent here or a full config. Defaults and unknown-ID rejection remain in Rust
`StrategyConfig::default_for_id`; this MR does not and must not restore an adapter-side default map.
Product `v1.5.62` deployed this producer contract and bounded direct/MCP smoke accepted the string ID.
Product `v1.5.63` deployed the optimizer starvation fix and passed product-owned stability checks while
the optimizer was active.

The separate product multi-symbol API work is also a prerequisite for live `6981.T` calls. Product CI
status is evidence owned by that repository; this MR only claims producer compatibility after the exact
HTTP contract is deployed and cross-repo verification reruns.

## Contract

- `GET /api/quote?symbol=...`
- `GET /api/kline?symbol=...&interval=...`
- `GET /api/signals?symbol=...`
- `GET /api/trend?symbol=...`
- `POST /api/backtest/historical`: symbol, string strategy ID, interval, days, risk params, optional cash
- `POST /api/backtest/benchmark`: symbol, interval, risk params, optional cash, existing history policy

Benchmark remains compute-expensive, non-destructive and disabled from default Gateway chat tool access.
News and sentiment remain global. Gateway analyze is outside this multi-symbol tool contract.

## Verification

- Red: Python 19 failed / 3 passed; TypeScript 18 passed / 2 failed / 1 collection error.
- Focused green: Python 48 passed; TypeScript 29 passed / 0 failed / 135 assertions.
- Full Python: 230 passed / 1 opt-in live-provider smoke skipped.
- Bun packages: 38 passed / 0 failed / 152 assertions; typecheck and pi/dsh builds passed.
- Python sdist/wheel build passed (46/23 files); pi/dsh npm dry-runs each contain only four expected files.
- Publication, secret, workstation-path, strategy-copy, sibling-import and mutation-boundary audits passed.
- Branch and merge-request pipelines passed; the Draft MR has no conflicts and remains unmerged.
- Version TDD red: Python 2 failed / 6 passed; TypeScript 1 failed on explicit stale `0.2.0` checks.
- Version focused green: Python 9 passed; TypeScript 1 passed with package/runtime/capabilities `0.3.0`.
- Version full gates: Python 230 passed / 1 skipped; Bun 39 passed / 153 assertions; typecheck and both
  builds passed. CLI, wheel and all package manifests report `0.3.0`.
- `0.3.0` sdist/wheel contain 46/23 files; pi/dsh dry-runs contain four expected files each; publication,
  secret, local-path, strategy-copy and internal-import audits passed.
- No production product call was made during version preparation.
- Production attempt 1 recorded producer runtime starvation before direct quote completed; no later tool
  ran and the timeout was not attributed to the adapter.
- After restart, direct quote/kline/string-ID historical passed. MCP later crossed a second starvation
  window, then kline retry and historical passed after another operator restart.
- A clean MCP-only retry passed quote, 15m kline and string-ID historical continuously; schema and
  no-trading-mutation checks passed. Evidence contains no price, candle, trade, metrics or response body.
- Product `v1.5.63` post-hotfix acceptance repeatedly exercised health and `6981.T` quote while the
  optimizer was active; all requests returned 200 with correct identity and bounded low-millisecond
  latency. Raw logs, exact process metrics and environment identifiers are omitted.

## Rollout and rollback

1. Push this final sanitized evidence and wait for the Agent MR pipeline to succeed.
2. Mark the MR ready without enabling auto-merge.
3. Keep dsh experimental; do not merge, tag or deploy in this step.

Rollback redeploys the prior adapter. It requires no strategy/default migration and performs no product
data mutation. A producer mismatch must fail explicitly; it must not be hidden with adapter defaults.

## Reviewer checklist

- [x] Confirm `quant_trade!152` is merged into product `main`.
- [x] Confirm product `v1.5.62` deployed the producer contract.
- [x] Review bounded direct/MCP smoke and producer-starvation attribution.
- [x] Confirm product `v1.5.63` optimizer hotfix deployment and stability acceptance.
- [ ] Confirm no local strategy default map or Rust engine logic exists.
- [ ] Confirm exact request, unknown-symbol and cross-interface parity tests.
- [ ] Confirm no order/cancel/broker capability and benchmark expensive policy remains.
- [ ] Confirm dsh is still experimental.
- [ ] Confirm pipeline and discussions satisfy protected-main Git Flow.
