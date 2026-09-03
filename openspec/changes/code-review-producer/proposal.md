# Proposal: Code Review Producer

## Problem

`quant_trade` must not retain an LLM provider, prompt, or local coding-agent orchestration. Product
code-review and review-response requests therefore need a versioned, provider-neutral producer in the
Intelligence Plane instead of a product-local model client.

## Scope

- Add `POST /v1/review/code` for a bounded diff plus optional project context.
- Add `POST /v1/review/respond` for a bounded message plus optional context.
- Use the existing provider-neutral `StructuredModelExecutor` with forced structured tool output.
- Return strict v1 response envelopes with provenance and warnings.
- Advertise `code_review` and `review_response` only after both implementations are complete.
- Publish exact runtime-compatible OpenAPI schemas and consumer contract tests.

## Non-goals

- No GitLab credential, comment, issue, merge-request, approval or mutation API.
- No repository checkout, filesystem edit, command execution or coding-agent loop.
- No database access and no import from the sibling product repository.
- No order, cancel, broker or trading mutation capability.
- No persistence of diffs, context, review messages or model output.

## Acceptance

- Request models forbid unknown fields, blank required text and values above frozen limits.
- Model calls and prompts exist only in this repository and use forced structured schemas.
- Diff, project context, message and response context are treated as untrusted data, never instructions.
- Review verdict is exactly `LGTM|NEEDS_CHANGES`; all structured output has exact keys and bounded text.
- Provider configuration, timeout, 429, transport and malformed output reuse the Gateway error envelope.
- Existing analyze, chat, wish and enrichment contracts do not regress.
- Full Python and TypeScript gates, builds, snapshot compatibility and side-effect boundary audits pass.
