# Standard Multi-Harness Agent

## Why

The extracted repository is only a CLI adapter prototype. Its MCP module is a
stub, its model story is implicit in the host harness, and the pi/dsh packages
cannot be treated as verified, independently publishable integrations.

The project needs a stable agent core that:

- consumes `quant_trade` only through versioned HTTP contracts;
- exposes real MCP tools over stdio and Streamable HTTP;
- works with harness-managed models in pi, dsh, Codex, Claude Code, Cursor and
  other MCP hosts;
- offers an optional standalone OpenAI-compatible agent runtime for GPT,
  DeepSeek, Kimi, MiniMax, Ollama and future providers;
- keeps trading execution disabled by default and clearly separates read-only
  and compute-heavy tools.

## What Changes

- Add a typed `QuantTradeClient` and a single Python tool registry.
- Replace the MCP stub with the official MCP Python SDK v2 server.
- Add `agent-tools mcp` and `agent-tools chat` commands.
- Add OpenAI-compatible provider presets with environment overrides.
- Add a small tool-calling agent loop for standalone/headless use.
- Make TypeScript adapters consume the local installed Python entry point.
- Fix root TypeScript build configuration and deterministic local tests.
- Keep dsh support experimental until a real profile exposes and calls a tool.

## Non-Goals

- No broker order placement.
- No duplication of indicators, signals, backtests or LangGraph logic from
  `quant_trade`.
- No provider-specific SDK dependency.
- No claim of dsh production compatibility before end-to-end verification.

## Success Criteria

- Python tests prove the API client, tool registry, MCP server and provider
  payload/response contracts.
- TypeScript tests run without a published PyPI package.
- `agent-tools mcp` exposes all tools through a real MCP server.
- `agent-tools chat --provider deepseek|kimi|openai|custom` can complete a
  tool-calling turn against a mocked OpenAI-compatible endpoint.
- pi uses the same canonical schemas; dsh remains isolated behind its adapter.
