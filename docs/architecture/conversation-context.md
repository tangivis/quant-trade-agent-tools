# Conversation Context Boundary

Status: current
Last updated: 2026-09-03

## Ownership

The Product/Data/Domain Plane owns durable users, threads, messages, selected symbols, retention and
summary watermarks. The Intelligence Plane owns prompt construction and stateless summarization. It does
not read the product database.

## Gateway Contract

`POST /v1/chat` accepts a current message, `9984.T|6981.T`, recent ordered history and optional bounded
`context_summary`. The runtime treats all supplied context as untrusted data and discards it after the
request.

`POST /v1/summarize/conversation` accepts an optional previous summary and bounded ordered messages. It
uses forced structured output and returns a non-empty simplified-Chinese summary with contract version,
provider provenance and warnings. It has no market tools, persistence or external mutation capability.

## Harness Contract

`conversation_create`, `conversation_context` and `conversation_append` are canonical CLI/MCP/pi/dsh
tools that call the protected `quant_trade` Conversation API. Authentication is supplied at runtime through
the product API token environment, never committed to this repository.

This design lets multiple harnesses share the same product-owned context without sharing local session
files, importing source code or coupling to a specific model provider.
