# Tasks

## SDD

- [x] Read AGENTS, current handoff and frozen parent contract.
- [x] Freeze opt-in/key gates, safe report allowlist and three staging calls.
- [x] Write the multi-file implementation plan.

## TDD

- [x] Add red test proving default gate never constructs the service.
- [x] Add red test proving missing key never constructs the service.
- [x] Add red mock test for translation + wish clarifying/confirming and safe summary.
- [x] Add red failure/redaction and no-mutation source audit tests.
- [x] Add a default-skipped real-provider live test.
- [x] Implement the minimal staging runner and CLI module entry point.

## Snapshot parity TDD

- [x] Add red tests requiring `/v1/chat` and `/v1/capabilities` in the producer snapshot.
- [x] Make the parity verifier method-aware without weakening required routes.
- [x] Add strict runtime response models and exact snapshot components for both routes.

## Documentation and verification

- [x] Register non-secret environment toggles in `.env.example`.
- [x] Update README, CHANGELOG, verification report and handoff.
- [x] Run focused/default full Python with live test skipped.
- [x] Run Bun tests/typecheck/build, `uv build`, package and boundary audits.
- [x] Run one explicit MiniMax live smoke after all mock/full gates pass.
- [x] Record only sanitized provider/model/contract/latency/shape results.
- [x] After the live smoke, add the standalone `docs/mr/` draft with dependency, evidence, rollout and
      limitations; do not create or push an actual MR.
