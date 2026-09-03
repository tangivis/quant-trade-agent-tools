# Standard Multi-Harness Agent Implementation Plan

## Objective

Turn the extracted adapter prototype into an independently versioned agent
package that consumes `quant_trade` through HTTP, exposes real MCP tools, works
across harnesses, and optionally runs with any OpenAI-compatible model.

## TDD Sequence

1. Freeze the current failures and desired contracts in Python and TypeScript
   tests.
2. Introduce `QuantTradeClient`; migrate CLI functions without changing public
   command names.
3. Build the canonical tool registry and register it with MCP SDK v2.
4. Add provider presets plus a bounded tool-calling loop.
5. Add `mcp` and `chat` CLI commands.
6. Make local TS tests independent of PyPI and restore root type checking.
7. Build both native adapters and document dsh as experimental.

## Verification Gates

- Python unit and integration-contract tests pass.
- MCP tools are discoverable through an in-memory SDK client.
- Provider tests never call a live model API.
- TypeScript tests, typecheck and builds pass with bun.
- The package contains no secret, database URL, cookie or order execution tool.

## Deferred

- Remote MCP OAuth and production deployment.
- dsh 1.0 end-to-end certification.
- Broker execution tools and human approval workflow.
- Generic multi-symbol trading logic in `quant_trade` itself.
