# Tasks

## 1. SDD

- [x] Inspect current structured executor, v1 models/routes, snapshot and capability tests.
- [x] Freeze request/output bounds, exact capability names and no-side-effect ownership.
- [x] Write the multi-file implementation plan.

## 2. Service TDD

- [x] Add red tests for normal code review and review response calls.
- [x] Add red tests for exact tool schema, untrusted-input prompt boundary and provenance.
- [x] Add red tests for invalid verdict, missing/extra keys, blank/overlong output.
- [x] Add red tests for provider config, timeout, 429 and malformed provider output.
- [x] Implement both methods by reusing `StructuredModelExecutor`.

## 3. Route and contract TDD

- [x] Add red route tests for strict shapes, blank/over-limit requests and common response metadata.
- [x] Add red capability tests for `code_review` and `review_response`.
- [x] Add red OpenAPI required-route and exact runtime/snapshot compatibility tests.
- [x] Implement Pydantic contracts, injectable routes, capabilities and snapshot.

## 4. Documentation and verification

- [x] Update README, architecture, detailed contract docs, CHANGELOG, MR draft and handoff.
- [x] Run focused and full Python suites.
- [x] Run TypeScript tests, typecheck and builds plus `uv build`.
- [x] Run package/snapshot checks, `git diff --check` and no-side-effect boundary audit.
