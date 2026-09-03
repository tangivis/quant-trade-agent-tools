# Standard Agent Requirements

## Requirement: Independent API Boundary

The agent MUST access `quant_trade` only through configured HTTP endpoints and
MUST NOT import its source modules or access its database.

### Scenario: authenticated remote backend

- GIVEN `QUANT_TRADE_API_TOKEN` is set
- WHEN any tool calls the backend
- THEN the request includes `Authorization: Bearer <token>`.

### Scenario: news normalization

- GIVEN the upstream news endpoint returns a JSON array
- WHEN the `news` tool completes
- THEN the public result is an object with an `articles` array.

### Scenario: bounded kline output

- GIVEN the upstream kline endpoint returns more candles than requested
- WHEN `kline.count` is provided
- THEN the public result contains only the newest requested candles.

### Scenario: historical backtest mapping

- GIVEN a supported strategy id and `days`
- WHEN the `backtest` tool runs
- THEN the client sends a valid tagged `StrategyConfig` to
  `/api/backtest/historical`.

### Scenario: benchmark filtering

- GIVEN `strategy` and `top`
- WHEN the upstream benchmark completes
- THEN results are filtered to the requested strategy and bounded by `top`.

## Requirement: Real MCP Server

The package MUST expose its tools through the official MCP Python SDK.

### Scenario: MCP discovery

- WHEN an MCP client lists tools
- THEN it sees the nine canonical tools with typed schemas.

### Scenario: MCP invocation

- WHEN an MCP client calls `quote`
- THEN the call passes through `QuantTradeClient` and returns backend JSON.

## Requirement: Multi-Model Standalone Agent

The standalone runtime MUST support OpenAI-compatible endpoints without
provider SDK coupling.

### Scenario: provider preset

- GIVEN `LLM_PROVIDER` is `openai`, `deepseek`, `kimi`, `minimax` or `ollama`
- WHEN configuration is resolved
- THEN a provider-specific default base URL and model are selected.

### Scenario: custom provider

- GIVEN `LLM_PROVIDER=custom`, `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`
- WHEN the agent sends a turn
- THEN it uses those configured values.

### Scenario: tool-calling turn

- WHEN the model requests a canonical tool
- THEN the agent executes it, appends the tool result, and requests a final
  answer within the configured iteration limit.

## Requirement: Harness Isolation

Platform adapters MUST remain thin and MUST NOT contain market logic.

### Scenario: pi package

- WHEN pi loads the package
- THEN nine `quant_*` tools delegate to the canonical CLI bridge.

### Scenario: dsh package

- WHEN dsh compatibility is not end-to-end verified
- THEN documentation and package metadata label it experimental.

## Requirement: Safe Trading Scope

The public agent MUST NOT expose broker order placement in this change.

### Scenario: tool listing

- WHEN any harness lists tools
- THEN no create-order, cancel-order or strategy-live mutation tool is present.
