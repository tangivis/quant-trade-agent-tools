# Code Review Producer — Implementation Plan

## Scope

Only modify `quant-trade-agent-tools`. Add two stateless v1 producer endpoints so the product runtime
can remove its remaining provider, prompt and local coding-agent ownership. No sibling, GitLab,
database, filesystem or trading mutation belongs in this slice.

## Red -> Green -> Refactor

1. Add application-service tests for review and respond happy paths, exact structured schemas,
   provider provenance and untrusted-input prompt isolation.
2. Add failure tests for invalid verdicts, missing/extra keys, blank/overlong output, provider config,
   timeout, 429 and malformed provider payloads.
3. Add route tests for strict request bounds, response envelopes, request IDs and fake-service
   injection.
4. Add capability and OpenAPI tests requiring both new routes without weakening existing routes.
5. Run the focused tests and retain implementation-missing failures as red evidence.
6. Add strict Pydantic models and the minimal `GatewayIntelligenceService` methods using the shared
   `StructuredModelExecutor`.
7. Add the two FastAPI routes and advertise capabilities only after the implementation is callable.
8. Regenerate the producer OpenAPI snapshot from runtime and rerun exact compatibility tests.
9. Refactor shared exact-key/text validation only if it preserves all existing task behavior.
10. Update README, architecture, detailed functions, CHANGELOG, MR draft, verification report and
    handoff with the frozen quant-core contract.
11. Run focused/full Python, all TypeScript gates, both builds, package inspection, boundary audit and
    `git diff --check`.

## Rollback

Both routes are additive and stateless. The product can disable its consumer routes without data
migration. Rollback must never reintroduce a product-local provider, prompt or coding-agent loop; use
an earlier compatible Gateway release or deterministic degraded behavior instead.
