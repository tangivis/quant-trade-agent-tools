# Tasks

## 1. SDD

- [x] Define service ownership and dependency direction.
- [x] Define REST contracts, security and error semantics.
- [x] Define phased migration and rollback strategy.
- [x] Write the implementation plan and architecture decision document.

## 2. Gateway TDD

- [x] Add failing tests for optional dependency loading and CLI registration.
- [x] Add failing tests for health and capability endpoints.
- [x] Add failing tests for Bearer authentication.
- [x] Add failing tests for context collection and partial failures.
- [x] Add failing tests for analyze response and error envelopes.
- [x] Add failing tests for stateless chat and expensive-tool policy.
- [x] Implement the minimal Gateway facade.

## 3. Legacy Compatibility TDD

- [ ] Add contract fixtures from current `/agent/analyze` output.
- [x] Add failing tests for `LegacyAnalysisProvider` request mapping.
- [x] Implement legacy provider mode.
- [ ] Add shadow comparison models and tests.

## 4. Product Integration

- [ ] Write a separate `quant_trade` OpenSpec change.
- [ ] Add reverse-proxy routing with rollback configuration.
- [ ] Add frontend API client behind a feature flag.
- [ ] Verify same-origin auth and no browser secrets.

## 5. Native Orchestration

- [ ] Specify parity thresholds and evaluation fixtures.
- [ ] Implement native provider via TDD.
- [ ] Run shadow evaluation and document results.
- [ ] Cut over only after explicit approval.

## 6. Verification

- [x] Run Python and TypeScript full suites.
- [x] Run Gateway contract, auth and failure tests.
- [ ] Run clean deployment smoke tests.
- [x] Update README, changelog and compatibility matrix.
