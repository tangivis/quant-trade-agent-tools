# Tasks

## 1. SDD

- [x] Define repository boundary and compatibility surface.
- [x] Define MCP, provider and safety requirements.
- [x] Write implementation plan.

## 2. Python TDD

- [x] Add failing tests for `QuantTradeClient` configuration and auth.
- [x] Add failing tests for canonical tool dispatch.
- [x] Add failing tests for MCP discovery and invocation.
- [x] Add failing tests for provider presets and custom configuration.
- [x] Add failing tests for a bounded tool-calling agent turn.
- [x] Implement the client, tools, MCP server and agent runtime.

## 3. TypeScript TDD

- [x] Make spawn tests use the local Python project deterministically.
- [x] Add the missing root TypeScript project references.
- [x] Fix shell build command execution and error propagation.
- [x] Keep pi adapter green and dsh explicitly experimental.

## 4. Verification

- [x] Run all Python tests.
- [x] Run all TypeScript tests and type checks.
- [x] Build pi and dsh packages.
- [x] Verify package metadata contains no secrets or workspace-only dependency.
- [x] Update README, architecture, changelog and investigation handoff.

## 5. Upstream Contract Audit

- [x] Add failing tests for news array normalization.
- [x] Add failing tests for bounded kline results.
- [x] Add failing tests for historical backtest request mapping.
- [x] Add failing tests for benchmark filtering and timeout.
- [x] Remove stale direct-import wording from adapter schemas.
- [x] Add detailed function and architecture documentation.
