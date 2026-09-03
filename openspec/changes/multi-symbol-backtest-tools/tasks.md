# Tasks

## 1. SDD

- [x] Audit current client, registry, CLI, MCP and TypeScript schema duplication.
- [x] Define supported symbol/interval enums and global-feed semantics.
- [x] Write the multi-file implementation plan before tests or runtime changes.

## 2. TDD red

- [x] Add exact HTTP request tests for all six symbol-scoped tools.
- [x] Add unknown-symbol/no-network and interval/risk validation tests.
- [x] Add ToolRegistry and real MCP schema parity tests.
- [x] Add TypeScript bridge plus pi/dsh snapshot parity tests.
- [x] Add explicit no-trading-mutation and no-copied-strategy-default tests.
- [x] Record the focused red failures.

## 3. Minimal implementation

- [x] Implement client enum validation and product request mapping.
- [x] Update ToolRegistry schemas and handlers.
- [x] Update CLI options/JSON object parsing and MCP typed functions.
- [x] Update TypeScript schema/object serialization; keep pi/dsh thin.
- [x] Make global news/sentiment semantics explicit.

## 4. Documentation and verification

- [x] Update README, ARCHITECTURE, detailed functions, harness skill and CHANGELOG.
- [x] Run focused and full Python tests.
- [x] Run Bun tests, typecheck and both builds.
- [x] Inspect release artifacts and run publication/secret/boundary audits.
- [x] Commit and immediately push dependency-safe conventional commits.
- [x] Create a non-merged MR targeting protected `main` with producer-first rollout dependency.

## 5. Version 0.3.0 release preparation

- [x] Record that product MR `quant_trade!152` is merged but production deployment is still pending.
- [x] Specify exact Python/TypeScript/runtime capability version propagation.
- [x] Add explicit failing Python and TypeScript `0.3.0` version tests.
- [x] Bump all package/runtime/lock metadata to `0.3.0` and keep contract version `v1`.
- [x] Update README, CHANGELOG, verification, MR and handoff release metadata.
- [x] Run focused/full tests, typecheck, builds and package/secret audits.
- [x] Commit and immediately push the version slice; keep MR `!4` Draft.

## 6. Post-deployment production smoke

- [x] Receive explicit confirmation that product `v1.5.62` is deployed.
- [x] Run bounded production loopback client/MCP quote, kline and historical backtest smoke.
- [x] Record both producer-starvation attempts and sanitized successful contract evidence without
  market/backtest payload bodies or environment coordinates.
- [x] Commit/push the `v1.5.62` smoke evidence while keeping MR `!4` Draft.
- [x] Receive explicit confirmation that product `v1.5.63` optimizer hotfix is deployed.
- [x] Accept product-owned stability evidence with the optimizer active and all bounded health/quote
  checks successful.
- [x] Commit/push final sanitized evidence, wait for the Agent pipeline, and mark MR `!4` ready.
- [x] Do not merge, tag or deploy.
