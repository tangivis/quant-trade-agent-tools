# Design: Real Provider Staging Smoke

## Command and gating

```bash
RUN_REAL_PROVIDER_E2E=1 uv run python -m agent_tools.staging_smoke
```

The runner checks the exact string `RUN_REAL_PROVIDER_E2E=1` first. It then selects an explicitly
configured provider, `LLM_PROVIDER`, or the first known provider with a present key. If the resolved
config has no key, it exits successfully with `status=skipped`. No service/client is constructed before
both conditions pass.

`RUN_REAL_PROVIDER_E2E` defaults to `0`; `REAL_PROVIDER_E2E_PROVIDER` defaults to empty. Neither is a
credential. The actual provider key remains in the existing vendor environment variable.

## Application boundary

The smoke constructs:

```text
resolve_provider(provider)
       -> GatewayIntelligenceService
       -> StructuredModelExecutor
       -> OpenAICompatibleStructuredClient
```

No new HTTP transport or provider schema is introduced.

## Calls and assertions

1. translation: Japanese input to `zh-CN`; validate a non-empty normalized translation and matching
   provider/model provenance.
2. wish clarifying: deliberately underspecified Chinese wish; require phase `clarifying`.
3. wish confirming: fully specified feature/priority/requirements request; require phase `confirming`
   and complete title/type/priority/requirements/summary.

The existing application services perform forced-tool and strict schema validation. The smoke adds
task-level expected phase and provenance checks.

## Safe report

Allowed fields:

```json
{
  "status": "passed|failed|skipped",
  "provider": "minimax",
  "model": "redacted-model-category",
  "contract": "agent-gateway-v1",
  "checks": [
    {
      "name": "translation",
      "latency_ms": 1234,
      "contract_valid": true
    }
  ]
}
```

Wish checks may add the public phase enum. Failed reports expose only normalized error code/status/
retryability or exception class; never exception text. Skipped reports expose a fixed reason code, not
environment contents.

## Pytest behavior

- Unit tests inject fake service/factory/clock and verify gate, call sequence and redaction.
- The live test skips unless the same runner gate passes.
- Default full suite therefore performs zero network calls.
- The explicit live test prints only `safe_report_json(report)`.

## Snapshot/runtime parity

The product verifier requires all product-facing v1 routes. The producer snapshot therefore includes
the already implemented `POST /v1/chat` and `GET /v1/capabilities` in addition to analyze, enrichment,
translation and wish. Runtime routes receive explicit response models so both paths have stable schemas.

The local parity test iterates the method actually present in each snapshot path instead of assuming
every operation is POST. It compares request bodies when present, successful responses, and every
published component schema exactly. Required routes are additive and are never removed to make a test
pass.

## Security boundary

The module imports no GitLab client and has no product URL or mutation method. Static audit rejects
GitLab credential/header, issue-creation, product mutation, DB and broker/order patterns in the runner.
