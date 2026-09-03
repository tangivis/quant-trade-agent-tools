# Tasks

## 1. SDD

- [x] Read current handoff, active OpenSpec set and documentation layout.
- [x] Define canonical public architecture/security ownership and internal-note marker semantics.
- [x] Write a multi-file implementation plan.

## 2. Publication test TDD

- [x] Add red tests for required root public documents and canonical sections.
- [x] Add red tests for README links and two-plane responsibility statements.
- [x] Add red tests for internal-only sanitized markers.
- [x] Add a redacted scanner for local paths, private hosts, environment IDs, internal hashes, live
  model evidence and token-like values.
- [x] Record the initial failures before documentation changes.

## 3. Public documentation

- [x] Add `ARCHITECTURE.md` and `SECURITY.md`.
- [x] Align README and CHANGELOG with public two-plane terminology.
- [x] Sanitize and mark handoff, MR draft and verification history.
- [x] Remove private repository coordinates from public package metadata and affected references.
- [x] Update detailed architecture/publish/migration documentation where the scan identifies drift.

## 4. Verification

- [x] Run focused publication tests and retain red/green evidence.
- [x] Run full Python and TypeScript suites, typecheck and both builds.
- [x] Inspect packages and rerun publication scan plus `git diff --check`.
- [x] Update verification, handoff and MR draft with final public-safe results.
