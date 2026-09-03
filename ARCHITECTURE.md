# Architecture

## Public positioning

`quant-trade-agent-tools` is the complete **Intelligence Plane** for a two-plane quantitative-trading
system. It owns model-facing behavior and exposes it through stable product and harness interfaces.

The independent `quant_trade` service is the **Product/Data/Domain Plane**. It owns product truth and
deterministic trading behavior. Neither repository imports the other, and neither is a submodule or
implementation layer of the other. They are peer deployable services with separate release cycles.

## Responsibilities

| Plane | Owns | Does not own |
|---|---|---|
| Intelligence Plane (`quant-trade-agent-tools`) | Provider adapters, deployment-time provider credentials, prompts, structured model execution, agent orchestration, REST Gateway, MCP/CLI, thin harness adapters | Product database, product UI, deterministic domain rules, Git hosting mutations, broker execution |
| Product/Data/Domain Plane (`quant_trade`) | Market and news facts, indicators, signals, backtests, persistence, product API/UI, deterministic risk and execution boundaries, product-owned external mutations | Provider credentials, model prompts, model routing, local coding-agent orchestration |

The Intelligence Plane can interpret and enrich product-supplied facts, but its output is advisory. The
Product/Data/Domain Plane remains authoritative for stored facts, validation, risk policy and execution.

## Layers inside the Intelligence Plane

```text
Product consumer ── versioned REST ─┐
                                    ├─> Application services ─> structured model boundary
MCP clients ── MCP ─────────────────┤             │
CLI / thin harness adapters ────────┘             └─> provider adapters
                         │
                         └─ versioned product HTTP APIs for facts/tools
```

1. **Provider adapters** normalize supported model protocols and read credentials only from the
   deployment environment.
2. **Application services** own prompts, forced structured schemas, validation and error normalization.
3. **REST Gateway** exposes versioned product contracts, request IDs, authentication and capability
   discovery.
4. **MCP and CLI** expose canonical read/analysis tools to general agent harnesses.
5. **Harness adapters** remain thin: they register tools, serialize arguments and return results without
   copying product or orchestration logic.

## External interfaces

### REST for product integration

The Product/Data/Domain Plane calls the Intelligence Plane through versioned HTTP endpoints. The
Intelligence Plane publishes the OpenAPI snapshot; the product consumer pins that snapshot and runs
compatibility tests. Requests contain only bounded contract data, never provider credentials.

REST covers native analysis, chat, stateless conversation summarization, enrichment, translation, wish
interpretation and side-effect-free code review/respond. Capability discovery advertises only implemented
tasks.

Conversation durability is deliberately outside this plane. `quant_trade` owns users, threads, messages,
symbols, rolling summaries and retention. The Gateway accepts only bounded caller-owned context and
discards it after each request.

### MCP, CLI and harnesses

MCP is the stable interface for model-capable harnesses. CLI is the stable interface for people,
scripts and thin adapters. pi, dsh and future harness packages must delegate to canonical contracts and
must not become alternate implementations of product logic or orchestration.

The three conversation tools are authenticated HTTP adapters to the protected product API. They do not
grant this repository database access and they do not turn the Gateway into a session server.

### Multi-symbol deterministic tool boundary

`quote`, `kline`, `signals`, `trending`, `backtest` and `benchmark` expose the exact supported symbol
enum `9984.T|6981.T`. Their interval boundary is `1m|5m|15m|1h|1d|1wk`; unknown values fail before an
HTTP call. Product news and aggregate sentiment endpoints remain global, so the corresponding tools do
not accept a symbol or imply per-symbol isolation.

Historical backtest requests forward a caller-supplied string strategy ID. The Intelligence Plane does
not expand IDs or copy Rust strategy defaults. Product MR `quant_trade!152` has landed the compatible
string-or-full-config producer on product `main`; ID defaults and unknown-ID rejection remain inside
Rust. The corresponding product release and optimizer isolation hotfix have passed bounded runtime
stability checks; future producer changes remain independently gated.
Benchmark retains its explicit expensive-tool policy and long timeout. Neither compute tool can place,
cancel or modify an order.

## Dependency direction

- The Intelligence Plane may call published Product/Data/Domain Plane HTTP APIs for facts and tools.
- The Product/Data/Domain Plane may call published Intelligence Plane REST APIs for model intelligence.
- Runtime integration never uses source imports, shared databases or filesystem coupling.
- Contract changes are producer-owned, versioned and verified in both repositories.
- A plane may degrade when its peer is unavailable, but it must not fabricate success or silently cross
  an ownership boundary.

This bidirectional HTTP relationship is not a dependency cycle at the code or persistence layer: each
request has a single owner, bounded contract and explicit failure behavior.

## Trust boundaries

- Product facts are untrusted until validated against the relevant request schema and task rules.
- Model output is untrusted until it passes exact structured-output validation.
- Prompts, history, diffs and context are bounded data; embedded instructions cannot authorize tools or
  mutations.
- User-derived conversation summaries are serialized at user privilege; only repository-owned policy may
  occupy a model system message.
- Browser clients never receive provider credentials or direct provider access.
- `approved`, `LGTM` and other model classifications are advisory values, not execution authorization.

## Reliability and evolution

The Product/Data/Domain Plane must continue deterministic operation when the Intelligence Plane is
unavailable. The Intelligence Plane must return explicit errors when facts or providers are unavailable;
it must not replace errors with a fabricated neutral decision.

Additive capabilities appear only after implementation and contract tests are green. Breaking contract
changes require a new version and coordinated consumer migration. Durable work, shadow evaluation and
harness stability are independent release concerns and must not be falsely advertised.

See [SECURITY.md](SECURITY.md) for credential, privacy, logging and vulnerability-reporting policy.
