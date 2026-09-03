# Design: Wish Interpretation Producer

## Ownership and runtime flow

```text
quant_trade /api/wish
        |
        | POST /v1/interpret/wish {message, history}
        v
GatewayIntelligenceService.interpret_wish
        |
        | StructuredModelExecutor + record_wish_interpretation
        v
provider-neutral structured output
        |
        v
strict phase-aware validation -> product-owned GitLab side effect
```

The producer has no persistence and no GitLab/product mutation credential. Every request is
self-contained; the model receives the complete ordered history plus the current message.

## Request contract

- `message`: required non-empty string, maximum 8000 characters.
- `history`: zero to 20 entries.
- entry `role`: only `user|assistant`.
- entry `content`: non-empty string, maximum 8000 characters.
- every request model uses `extra=forbid`.
- the application also honors a lower configured `TRADE_AGENT_MAX_HISTORY` limit.

## Structured output

The only forced tool is `record_wish_interpretation`:

```json
{
  "reply": "我帮你整理了需求，请确认提交。",
  "wish": {
    "phase": "confirming",
    "title": "K线多周期",
    "type": "feature",
    "priority": "medium",
    "requirements": ["支持 1m/5m/15m 周期切换"],
    "summary": "K线图支持多周期切换"
  }
}
```

Limits:

- reply: 1..4000;
- title: 1..200;
- summary: 1..4000;
- requirements: 1..20 for confirming/confirmed; each item 1..1000;
- phase: `clarifying|confirming|confirmed`;
- type: `feature|bug|refactor`;
- priority: `low|medium|high|urgent`;
- no unknown keys at either level.

For `clarifying`, structural fields may be omitted. Any supplied optional field is still validated.
For `confirming` and `confirmed`, all five structural fields are mandatory and non-empty. A bare
`{"phase":"confirmed"}` is always `MODEL_RESPONSE_ERROR`.

The prompt requires Simplified Chinese and explicitly says that a confirmation message must rebuild
the complete payload from history. The service enforces non-empty Chinese reply/title/summary and
rejects common Traditional-only characters; technical tokens inside requirements remain allowed.

## Response contract

```text
request_id + contract_version=v1
reply
wish
provenance(provider/model)
warnings
```

Clarifying responses omit absent optional wish fields. Provenance comes from resolved provider config;
warnings are application-owned. No model-supplied credential, issue body, URL or mutation result is
accepted.

## Failure behavior

- malformed structured output: `MODEL_RESPONSE_ERROR` 502, non-retryable;
- provider config: `PROVIDER_CONFIG_ERROR` 503;
- timeout: `MODEL_TIMEOUT` 504/retryable;
- 429: `MODEL_RATE_LIMIT` 503/retryable;
- other provider transport/status failures reuse `StructuredModelExecutor` mappings;
- invalid route body/history: existing `VALIDATION_ERROR` envelope.

## Capability and packaging

After runtime and contract tests are green, `wish_interpretation` is appended to
`intelligence_tasks`. `/v1/interpret/wish` and its component schemas are added to
`openapi/agent-gateway-v1.json`, which remains packaged in wheel/sdist.
