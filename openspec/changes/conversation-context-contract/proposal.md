# Conversation Context Contract

## Why

The product needs durable cross-Harness conversations without making the Intelligence Plane stateful.
The current chat contract accepts recent history but has no rolling summary field, and its runtime rejects
`6981.T` even though the tool layer supports that symbol.

## What Changes

- Add optional bounded `context_summary` to `POST /v1/chat`.
- Add `POST /v1/summarize/conversation` for a bounded, structured rolling summary.
- Expand analyze/chat symbol contracts to `9984.T` and `6981.T`.
- Add HTTP-only canonical conversation tools so Pi, DSH and MCP clients can use product-owned threads.

## Boundaries

- The Gateway never persists sessions or summaries.
- `quant_trade` owns authorization, conversation records and retention.
- Conversation tools only call published product REST endpoints.
- No adapter reads Pi, DSH or Codex local session files.

## Public-release acceptance findings

- Conversation summaries remain untrusted user-derived data and MUST NOT be promoted to a model system
  message.
- The canonical `analyze` tool MUST call this repository's native Gateway v1 contract rather than a
  product-owned legacy agent endpoint or caller-supplied live facts.
- Pi and DSH MUST both propagate harness cancellation to the owned CLI subprocess.
- The conversation additions and corrected canonical analyze contract MUST ship as `0.4.0`, newer than
  the immutable `v0.3.1` tag, with public repository metadata and accurate tool counts.
- Public delivery MUST use a sanitized public history; internal remotes, workstation paths and historical
  execution identifiers are not public release artifacts.
