<!-- visibility: internal-only; sanitized -->

# Public review blockers plan

## Objective

Repair the explicit legacy rollback and bind Gateway chat to its validated symbol before public delivery,
without changing REST schemas, product ownership or trading boundaries.

## Sequence

1. Preserve the review findings as failing client/provider/runtime/service tests.
2. Add the smallest separately named legacy product request method.
3. Add optional selected-symbol context and allowlisted missing-argument injection.
4. Run focused regressions, then full Python/TypeScript and release gates.
5. Deliver from latest internal `main` through a new feature MR; append only a sanitized tree commit to the
   still-open public PR.
6. Resolve the two public threads only after their exact tests and both pipelines pass, then merge under the
   requested zero-approval policy.

## RED/GREEN evidence

- RED: five focused tests failed: the dedicated legacy client method did not exist, the legacy provider
  called canonical analyze, the Gateway dropped its validated symbol, and the runtime neither accepted nor
  safely applied selected-symbol context.
- GREEN: the same five focused tests pass after the minimal implementation. The related client, Gateway,
  runtime and tool suite then exposed one stale app-level fake; updating it to the dedicated legacy
  protocol restored the complete related regression suite.
- Full GREEN: Python 249 passed / 1 opt-in live-provider case skipped; TypeScript 40 passed; Ruff,
  typecheck, pi/dsh builds, Python sdist/wheel, strict OpenSpec, public-documentation/release metadata,
  Bandit and Python/Bun dependency audits passed.
