# Conversation Context Contract Plan

## Goal

- Keep the Gateway stateless while accepting a caller-owned conversation summary.
- Add a bounded conversation-summary producer for `quant_trade` persistence.
- Support both `9984.T` and `6981.T` consistently in analyze and chat contracts.
- Expose product-owned conversation context through canonical CLI/MCP/Harness tools without database access.

## Sequence

1. Add failing model, route, service and OpenAPI tests.
2. Implement summary request/response contracts and provider orchestration.
3. Pass `context_summary` into the bounded agent runtime.
4. Remove the single-symbol chat restriction.
5. Add HTTP-only conversation client/tool adapters.
6. Update package schemas, docs, changelog and compatibility snapshots.
7. Run Python, TypeScript, typecheck and build verification.

## Public-release acceptance sequence

8. Preserve RED evidence for system-role summary injection, legacy analyze dispatch, missing Pi cancellation,
   stale version/metadata and the absent lint gate.
9. Keep caller-derived summaries at user privilege and migrate canonical analyze to the native v1 Gateway
   request without accepting caller facts.
10. Forward Pi cancellation and synchronize all package descriptions, repository URLs and version `0.4.0`.
11. Add a focused Ruff CI gate, resolve its configured error/import/modernization findings, and rerun all
    existing gates.
12. Inspect wheel, sdist and npm tarballs; scan the public snapshot and reachable public history plan for
    credentials, private coordinates, local paths and workspace runtime dependencies.
13. Deliver through a feature branch and reviewed public PR. Do not mirror internal branches or historical
    refs to the public repository.
14. Add a failing static workflow contract, then implement a credential-free GitHub pull-request gate with
    pinned action revisions, read-only permissions and no provider/registry secret dependency.
15. Require the successful public check on protected `main`; do not merge, tag, publish or deploy.

## Acceptance RED evidence

- Ad-hoc Ruff baseline: 26 failures under the intended `E4,E7,E9,F,I,UP` rule set.
- The current tests explicitly expected `/agent/analyze`, the Pi adapter ignored its available
  `AbortSignal`, release tests pinned the already-tagged `0.3.1`, and package descriptions still claimed
  nine read-only tools.
- Public-CI contract RED: `tests/test_release_metadata.py` failed because `.github/workflows/ci.yml` did
  not exist. The minimal workflow made all 13 release-metadata tests green.
- OpenSpec strict-validation RED: the active delta used plain requirement headers and was not parseable as
  a change delta. Converting it to `ADDED Requirements` with level-four scenarios preserved the contract
  and made strict validation green.

## Verification Result

- Python: `243 passed, 1 skipped`
- TypeScript adapters: `40 passed`
- Ruff, `bun run typecheck`, both adapter bundles and `uv build` passed
- Product cross-repository verifier accepted producer routes, consumer routes and both ownership boundaries
- Wheel isolated-install smoke reported `agent-tools 0.4.0`; pi/dsh npm dry-run archives each contained
  only four allowlisted entries and no workspace runtime dependency.
- Bun audited 247 packages with no known vulnerability; pip-audit found no vulnerable resolved dependency
  and skipped only this not-yet-published project identity; Bandit passed.
