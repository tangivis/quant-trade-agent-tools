# Wish Interpretation Producer — Implementation Plan

## Scope

Only modify `quant-trade-agent-tools`. Implement the stateless producer required by the frozen
cross-repo contract; `quant_trade` remains the sole owner of GitLab credentials and issue creation.

## Red → Green → Refactor

1. Write service tests for clarifying, confirming and confirmed responses, asserting that complete
   ordered history and current message reach the model boundary.
2. Write failure tests for incomplete confirmed output, malicious phase/type/priority, empty and
   overlong fields, unknown keys, timeout, 429 and provider failures.
3. Write route tests for strict request parsing, message/content/history limits, response envelope and
   capability discovery.
4. Write OpenAPI tests for the new path and exact component snapshots.
5. Run focused tests and retain the implementation-missing failures as red evidence.
6. Add phase-aware normalization to `GatewayIntelligenceService`, reusing its existing
   `StructuredModelExecutor` rather than adding a second provider transport.
7. Add strict Pydantic request/response models and the injectable Gateway route.
8. Advertise the capability only after the implementation exists; update the producer snapshot.
9. Refactor shared validation only where it reduces duplication without changing the four existing
   enrichment tasks or native analyze.
10. Update all affected documentation, OpenSpec tasks and cross-session handoff.
11. Run focused/full Python, Bun tests/typecheck/build, `uv build`, contract packaging and boundary
    audits.

## Rollback

The new route is additive. Rollback is removal/disablement at the `quant_trade` consumer feature
boundary; there is no producer-side persistence to migrate and no GitLab credential to revoke here.
