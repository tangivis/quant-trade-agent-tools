# Migration from the product repository

This repository was extracted so the Intelligence Plane can evolve and release independently from the
Product/Data/Domain Plane. The migration is complete; this document records the supported boundary for
maintainers and downstream consumers.

## Ownership after migration

`quant-trade-agent-tools` owns provider adapters, prompts, structured model execution, orchestration,
the versioned REST Gateway, MCP/CLI and thin harness adapters. It does not own the product database,
deterministic trading rules, product UI, Git hosting workflows or broker execution.

The independent product service owns market and news facts, indicators, signals, backtests,
persistence, deterministic risk and execution controls, and the product-facing UI/API. It does not
embed provider credentials, prompts or local coding-agent orchestration.

## Integration contract

- Runtime integration is HTTP-only and uses producer-owned, versioned contracts.
- The product calls Intelligence Plane REST endpoints for model-backed decision support.
- MCP clients and harnesses call canonical Intelligence Plane tools.
- The Intelligence Plane may call published product APIs for facts; it never imports product modules or
  accesses product storage.
- Each service can start independently and must report peer failures explicitly.

Consumers migrating from a colocated implementation should replace source imports and subprocess
coupling with the published REST, MCP or CLI interface that matches their use case. They should pin the
OpenAPI snapshot and run contract compatibility tests during upgrades.

## Security consequences

Provider credentials remain on the Intelligence Plane. Product, Git hosting, database and broker
credentials are out of scope. Model output is schema-validated advisory data; all persistence and
external mutation remain product-owned.

Historical workstation paths, private remote coordinates and environment-specific validation evidence
have been removed from this public migration record. See the repository root `ARCHITECTURE.md` and
`SECURITY.md` for the current canonical policies.
