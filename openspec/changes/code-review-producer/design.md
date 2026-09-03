# Design: Code Review Producer

## Ownership and flow

```text
quant_trade consumer
        |
        | versioned HTTP request containing text only
        v
GatewayIntelligenceService
        |
        | provider-neutral StructuredModelExecutor
        | forced record_code_review / record_review_response tool
        v
strict normalization -> v1 response (no producer side effect)
```

The product owns transport to the Gateway and any later GitLab behavior. This producer owns provider
resolution, prompts, structured output and validation. It does not run a coding agent, inspect a local
checkout or call any product/GitLab mutation.

## Request contracts

`POST /v1/review/code`:

- `diff`: required non-blank string, maximum 120000 characters.
- `project_context`: optional non-blank string, maximum 20000 characters.

`POST /v1/review/respond`:

- `message`: required non-blank string, maximum 8000 characters.
- `context`: optional non-blank string, maximum 20000 characters.

Both models use `extra=forbid`. Inputs are untrusted review material. Prompt-like text inside them is
content to inspect or answer about and cannot override the system task, request tools or authorize an
external action.

## Structured outputs

Code review uses the forced tool `record_code_review`:

```json
{
  "review": "Bounded actionable review text",
  "verdict": "NEEDS_CHANGES"
}
```

- exact keys only;
- `review`: non-blank, maximum 12000 characters;
- `verdict`: exactly `LGTM|NEEDS_CHANGES`.

Review response uses the forced tool `record_review_response`:

```json
{
  "reply": "Bounded response text"
}
```

- exact key only;
- `reply`: non-blank, maximum 8000 characters.

The prompts forbid repository/GitLab/database/trading mutation, command execution and claims that an
action was performed. The service accepts only the exact schema and appends provider/model provenance
and application-owned warnings.

## Response contracts

Every successful response includes `request_id`, `contract_version=v1`, `provenance(provider/model)`
and `warnings`.

- `/v1/review/code` additionally returns `review` and `verdict`.
- `/v1/review/respond` additionally returns `reply`.

The producer is stateless and has no persistence or mutation rollback. Consumer rollback is simply
disabling the product route/feature while retaining its non-LLM deterministic runtime.

## Failure behavior

- invalid request: existing `VALIDATION_ERROR` 422 envelope;
- provider config: `PROVIDER_CONFIG_ERROR` 503;
- timeout: `MODEL_TIMEOUT` 504/retryable;
- 429: `MODEL_RATE_LIMIT` 503/retryable;
- other provider HTTP failures: existing normalized model errors;
- missing, extra, invalid-enum, blank or overlong structured output: `MODEL_RESPONSE_ERROR` 502.

## Capability and OpenAPI

After implementation and route tests are green, append `code_review` and `review_response` to
`intelligence_tasks`. Add both routes and four request/response component schemas to
`openapi/agent-gateway-v1.json`; consumer compatibility tests compare runtime and snapshot exactly.
