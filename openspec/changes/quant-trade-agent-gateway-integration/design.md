# Design: Quant Trade Agent Gateway Integration

## Target Architecture

```text
Browser / Mobile / Product Client
               |
       HTTPS same-origin
               |
        nginx / reverse proxy
        +------+-----------------------------+
        |                                    |
   /api/* -> quant_trade Rust :5188     /agent-api/*
                                             |
                                   trade_agent Gateway :8010
                                   +---------------------+
                                   | REST API            |
                                   | ContextCollector    |
                                   | AgentRuntime        |
                                   | ToolRegistry        |
                                   | ProviderResolver    |
                                   +----------+----------+
                                              |
                         +--------------------+-------------------+
                         |                                        |
                 quant_trade Rust APIs                 Model provider APIs
                         |
             legacy backend_llm /agent/analyze
             (transition-only compatibility path)

Harnesses -> MCP stdio/HTTP -> same ToolRegistry
```

The reverse proxy, not the Rust application, owns routing to the Gateway. This
avoids an application-level Rust → agent → Rust proxy cycle and keeps browser
credentials/model keys out of frontend code.

## Component Ownership

| Component | Owner | Responsibility |
|---|---|---|
| Market data, indicators, signals | `quant_trade` Rust | Business truth and persistence |
| Backtest and benchmark algorithms | `quant_trade` Rust | Strategy computation |
| Legacy LangGraph | `quant_trade/backend_llm` | Transition baseline only |
| Tool contract and normalization | `trade_agent` | Stable cross-harness API |
| Agent orchestration | `trade_agent` | Context collection, tool policy, model loop |
| Product REST contract | `trade_agent` Gateway | `/v1/analyze`, `/v1/chat`, health/capabilities |
| TLS and same-origin routing | reverse proxy | External network boundary |
| Product UI | `quant_trade` frontend | Presentation; no model/tool secrets |

## Gateway Process

Proposed command:

```bash
uv run agent-tools gateway --host 127.0.0.1 --port 8010
```

Gateway dependencies SHOULD be optional, for example `uv sync --extra gateway`,
so CLI/MCP users do not install FastAPI/Uvicorn unnecessarily.

FastAPI is recommended because the existing Python ecosystem already uses
Pydantic/FastAPI, it produces OpenAPI automatically, and it is easy to test
in-process without opening network ports.

## REST Contracts

### `GET /health`

Returns process liveness only. It MUST NOT call model providers or expensive
upstream endpoints.

```json
{"status":"ok","version":"0.3.0"}
```

### `GET /v1/capabilities`

Returns gateway version, supported symbols, tool names, transports, provider
names, contract version and whether legacy analysis fallback is enabled. It
MUST NOT expose API keys, upstream tokens or internal URLs.

### `POST /v1/analyze`

Minimal request:

```json
{
  "symbol": "9984.T",
  "question": "当前风险和可能的交易方向是什么？",
  "mode": "standard"
}
```

The client MUST NOT supply live price, RSI, ADX or sentiment as authoritative
values. `ContextCollector` fetches quote, trend, signals, sentiment and recent
news from `quant_trade`, timestamps the snapshot, and passes that structured
context into the selected orchestration provider.

The response MUST separate facts, interpretation and decision support:

```json
{
  "request_id": "...",
  "symbol": "9984.T",
  "as_of": "...",
  "facts": {},
  "analysis": {},
  "decision": {
    "action": "HOLD",
    "confidence": 0.55,
    "approved": false,
    "risk_notes": []
  },
  "provenance": {
    "provider": "legacy|native",
    "model": "...",
    "tools": ["quote", "trending", "sentiment"]
  },
  "warnings": ["delayed_market_data", "decision_support_only"]
}
```

### `POST /v1/chat`

Stateless first release:

```json
{
  "message": "比较当前趋势和新闻情感",
  "history": [],
  "symbol": "9984.T",
  "allow_expensive_tools": false
}
```

The first release does not persist sessions. The caller may send bounded
history. `benchmark` is unavailable unless `allow_expensive_tools=true`;
order/cancel tools do not exist regardless of this flag.

## Authentication

- External authentication is primarily enforced by the reverse proxy.
- Gateway additionally supports `TRADE_AGENT_API_TOKEN` Bearer auth for
  defense in depth.
- Gateway uses `QUANT_TRADE_API_TOKEN` only for calls to upstream services.
- Provider keys remain server-side environment variables.
- Browser responses and logs MUST NOT contain any key or token.

## Context Collection

For `standard` analysis, requests SHOULD be parallelized where safe:

```text
quote ─────┐
trending ──┤
signals ───┼─> validated ContextSnapshot
sentiment ─┤
news ──────┘
```

Each source result includes capture time and error state. Partial context may
produce a response only when missing fields are explicitly listed in
`warnings`; live numbers are never synthesized.

## Orchestration Providers

An internal interface isolates migration:

```text
AnalysisProvider
  ├── LegacyAnalysisProvider -> backend_llm /agent/analyze
  └── NativeAnalysisProvider -> trade_agent model/tool orchestration
```

Configuration selects `legacy`, `native`, or `shadow`:

- `legacy`: production-compatible first release.
- `native`: new independent implementation.
- `shadow`: return legacy result, execute native in background/bounded task,
  compare structured fields, and record metrics without changing user output.

## Error Envelope

All REST errors use one object:

```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "行情服务超时",
    "request_id": "...",
    "retryable": true
  }
}
```

Provider 429, invalid model output, upstream JSON drift and iteration limits
MUST remain failures. They cannot be converted into a successful HOLD result.

## Observability

Record structured fields:

- request id, route, status, latency;
- analysis mode and provider/model name;
- tool names and per-tool latency;
- upstream/provider error class;
- legacy/native comparison fields in shadow mode.

Do not log prompt history, news bodies, tool arguments, tokens or model keys by
default. Optional debug logging requires explicit local configuration.

## Deployment

Recommended services:

```text
quant-trade-backend.service      Rust :5188
quant-trade-llm.service          legacy Python :8003 (transition)
trade-agent-gateway.service      new Gateway :8010
nginx                            public TLS / same-origin routing
```

The Gateway starts independently. A Gateway failure MUST NOT prevent the
market dashboard and Rust APIs from starting.

## Migration Phases

### Phase 0: Contracts

Freeze request/response schemas, fixtures and legacy output samples. No
runtime routing changes.

### Phase 1: Gateway Facade

Implement health/capabilities/analyze/chat. Analyze uses
`LegacyAnalysisProvider`; product behavior remains equivalent.

### Phase 2: Product Routing

Add reverse-proxy route and frontend client. Keep the existing UI path behind
a feature flag for immediate rollback.

### Phase 3: Native Shadow

Implement native orchestration, execute shadow comparisons, measure action,
confidence, approval, risk-note and latency differences.

### Phase 4: Native Cutover

Switch default to native only after agreed parity thresholds and soak period.
Legacy remains an explicit fallback for one release.

### Phase 5: Legacy Retirement

Remove product dependency on `backend_llm /agent/analyze`; retain only
business services still required elsewhere or delete them in a separate
`quant_trade` OpenSpec change.

## Rejected Alternatives

### Browser directly uses MCP

Rejected for the product UI: browser transport, auth, session lifecycle and
tool-call UX are unnecessary complexity. MCP remains the harness interface.

### `quant_trade` imports the agent Python package

Rejected: recreates source/runtime coupling and synchronized releases.

### Rust backend implements an agent reverse proxy

Rejected as the primary path: agent then calls Rust data APIs, creating an
application-level dependency cycle. Reverse proxy routing is operationally
simpler and keeps service ownership clear.

### Move all Rust business logic into the agent repo

Rejected: duplicates the source of truth and expands the agent security scope.
