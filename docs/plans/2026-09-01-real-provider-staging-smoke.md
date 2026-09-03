# Real Provider Staging Smoke — Implementation Plan

## Scope

Only modify `quant-trade-agent-tools`. Add an operator-invoked, quota-consuming verification path that
is impossible to trigger from default tests and that exercises the existing provider-neutral structured
application boundary without product or GitLab side effects.

## Red → Green → Refactor sequence

1. Write gate tests with a factory that raises if constructed; verify disabled and missing-key paths skip.
2. Write an enabled fake-service test requiring translation, wish clarifying and wish confirming in order.
3. Seed fake outputs/prompts/errors with canary secrets and assert the serialized report contains none.
4. Write source-boundary tests rejecting GitLab credential/client, issue creation, product mutation, DB,
   broker and order/cancel patterns.
5. Add a live pytest case that skips unless both gate conditions pass.
6. Add snapshot red tests that require `/v1/chat` and `/v1/capabilities`, compare their runtime methods
   and contracts, and retain all existing required routes.
7. Run focused tests to retain missing-module/function and missing-route red evidence.
8. Implement `agent_tools.staging_smoke` with injectable environment, factory and monotonic clock.
9. Add strict chat/capabilities response models, make the verifier GET/POST-aware, and update snapshot
   path/components exactly.
10. Keep the report schema allowlisted; never serialize service results or raw exception messages.
11. Update environment examples and operator documentation.
12. Run focused/full Python, TypeScript tests/typecheck/build, Python build/package inspection and diff/
    security audits with live calling disabled.
13. Explicitly set the opt-in flag and MiniMax provider, run exactly one live smoke, and record only the
    safe report fields.
14. Only after that live run, write the independent `docs/mr/` draft with branch metadata,
    producer-first ordering, contract/security evidence, full verification, rollout/rollback and explicit
    dsh/shadow/durable-worker limitations. Do not invoke GitLab or Git write operations.

## Abort behavior

If the real provider returns a normalized error, invalid phase/shape, or rate limit, report the safe error
and do not retry automatically. This keeps staging cost bounded and avoids hiding provider incompatibility.
