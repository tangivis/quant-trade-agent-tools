# Design

## Stateless Flow

`quant_trade` sends `context_summary`, recent ordered messages, the current message and symbol. The Gateway
constructs the model context for that request and discards it after completion.

The summary producer accepts a previous summary plus bounded ordered messages and returns a validated plain
text summary. It has no tool access and no persistence.

## Harness Flow

Canonical `conversation_create`, `conversation_context` and `conversation_append` tools call the protected
product REST API with `QUANT_TRADE_API_TOKEN`. Pi and DSH continue to register schemas through their existing
thin adapters.

## Safety

- Summary and message fields have explicit length and count limits.
- Stored conversation content is untrusted data and cannot grant tool authorization. The chat runtime
  serializes `context_summary` as untrusted user-role data after the fixed system policy; it never creates
  a second system message from caller-controlled content.
- Product-native chat excludes conversation mutation tools from its internal tool loop.

## Native analysis tool boundary

The model-facing `analyze` tool sends only `symbol`, optional `question`, and fixed `mode=standard` to
`POST /v1/analyze` on the Intelligence Plane Gateway. It does not accept caller-supplied price, RSI, ADX,
regime or sentiment as facts. The Gateway collects those facts from the Product/Data/Domain Plane and
returns the layered v1 response. Product API and Gateway credentials remain separate environment inputs.

## Harness and release hardening

- Both harness adapters forward cancellation into the shared Node subprocess bridge.
- Published adapters bundle the private workspace bridge and require only their host peer, Node, `uvx`,
  the public Python distribution and configured HTTP services at runtime.
- Python lint rules covering errors, imports and modern typing execute in CI.
- Public package metadata points only to the public GitHub repository. The `0.4.0` minor version identifies
  the corrected pre-1.0 canonical analyze contract and does not reuse the existing `v0.3.1` artifact identity.
- Public pull-request CI installs from checked-in locks and runs the same credential-free Python and
  TypeScript acceptance gates. External actions are pinned by commit SHA, workflow permissions are
  read-only, and real-provider smoke and registry-publication paths remain disabled.
