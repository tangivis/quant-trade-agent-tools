# Agent Gateway Requirements

## Requirement: Optional Product Gateway

The package MUST provide an optional REST Gateway without making Gateway
dependencies mandatory for CLI or MCP installations.

### Scenario: minimal CLI/MCP install

- GIVEN the package is installed without the Gateway extra
- WHEN CLI or MCP is used
- THEN no FastAPI/Uvicorn dependency is required.

### Scenario: Gateway startup

- GIVEN the Gateway extra is installed
- WHEN `agent-tools gateway` starts
- THEN it binds to the configured host/port and defaults to loopback.

## Requirement: Health and Capability Discovery

### Scenario: health probe

- WHEN `/health` is requested
- THEN the process returns liveness without calling market or model services.

### Scenario: capability discovery

- WHEN `/v1/capabilities` is requested
- THEN the response identifies contract version, supported tools, providers,
  symbols and orchestration modes without exposing secrets.

## Requirement: Server-Owned Market Context

### Scenario: analyze request

- GIVEN a client requests analysis for `9984.T`
- WHEN `/v1/analyze` runs
- THEN the Gateway collects current quote, K-line indicators, trend, signals,
  sentiment and news
  from configured `quant_trade` APIs.

### Scenario: caller supplies live-looking numbers

- GIVEN a client attempts to provide price, RSI, ADX or sentiment as facts
- WHEN the request is validated
- THEN those fields are rejected or treated only as non-authoritative notes.

### Scenario: partial upstream failure

- GIVEN one context source fails
- WHEN sufficient context remains for analysis
- THEN the missing source is listed in warnings and no missing value is
  fabricated.

## Requirement: Stable Analyze Contract

### Scenario: successful analysis

- WHEN `/v1/analyze` succeeds
- THEN facts, analysis, decision, provenance and warnings are separate
  structured fields.

### Scenario: failed analysis

- WHEN upstream data, provider output or orchestration validation fails
- THEN the Gateway returns a structured error and MUST NOT convert it to a
  successful HOLD response.

## Requirement: Stateless Chat First Release

### Scenario: bounded history

- GIVEN the caller supplies bounded history
- WHEN `/v1/chat` runs
- THEN the Gateway uses it for the current request but does not persist it.

### Scenario: expensive tools disabled

- GIVEN `allow_expensive_tools=false`
- WHEN the model attempts to call benchmark
- THEN the policy rejects the call before starting the upstream grid search.

## Requirement: Shared Tool Contract

### Scenario: REST and MCP parity

- WHEN REST or MCP needs market tools
- THEN both use the same `ToolRegistry`, normalization and safety metadata.

### Scenario: schema drift

- WHEN a canonical tool schema changes
- THEN contract tests fail until REST, MCP and TypeScript snapshots agree.

## Requirement: Migration Compatibility

### Scenario: legacy mode

- GIVEN orchestration mode is `legacy`
- WHEN analysis runs
- THEN the Gateway uses the existing `backend_llm /agent/analyze` provider.

### Scenario: shadow mode

- GIVEN orchestration mode is `shadow`
- WHEN analysis runs
- THEN legacy output remains user-visible while native output is compared
  without influencing the response.

### Scenario: rollback

- GIVEN native mode causes regressions
- WHEN configuration is switched to legacy
- THEN service behavior can be restored without a frontend deployment.

## Requirement: Authentication and Secret Isolation

### Scenario: protected deployment

- GIVEN `TRADE_AGENT_API_TOKEN` is configured
- WHEN a request lacks a valid Bearer token
- THEN the Gateway rejects it before tool or model calls.

### Scenario: browser response

- WHEN any response or error is generated
- THEN provider keys, upstream tokens and internal credentials are absent.

## Requirement: No Broker Execution

### Scenario: public capabilities

- WHEN capabilities or tools are listed
- THEN no order, cancel, position mutation or live-strategy mutation operation
  is exposed.
