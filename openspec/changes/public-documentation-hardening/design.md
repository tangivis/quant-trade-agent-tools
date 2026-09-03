# Design: Public Documentation Hardening

## Documentation hierarchy

```text
README.md          public landing page and capability summary
ARCHITECTURE.md    canonical system boundaries and dependency direction
SECURITY.md        canonical security/privacy policy and reporting guidance
docs/*             detailed public references or explicitly marked sanitized internal execution notes
OpenSpec/plans     design history, still subject to publication-safety scanning
```

`ARCHITECTURE.md` and `SECURITY.md` are stable public contracts. Handoffs, verification reports and MR
drafts are operational history, so they carry an HTML visibility marker. The marker is not an exemption
from redaction: every text artifact remains subject to high-risk publication scanning.

## Public architecture vocabulary

- **Intelligence Plane (`quant-trade-agent-tools`)**: provider adapters, credentials at deployment,
  prompts, structured model execution, orchestration, REST Gateway, MCP/CLI and thin harness adapters.
- **Product/Data/Domain Plane (`quant_trade`)**: product UI/API, facts, deterministic trading-domain
  logic, persistence, risk/execution boundaries and product-owned external mutations.
- The planes are peer deployable services, not a source-code inheritance hierarchy.
- Runtime integration is only through versioned HTTP contracts; consumers pin OpenAPI snapshots and
  run compatibility tests.
- Product unavailability must not make the Intelligence Plane fabricate facts; Intelligence Plane
  unavailability must not stop deterministic product operation.

## Security vocabulary

- Provider credentials stay in Intelligence Plane deployment secrets and never enter requests,
  responses, browser state or documentation examples.
- Product/database/external-service credentials stay with the Product/Data/Domain Plane.
- The Intelligence Plane does not directly access product databases or mutate GitLab, repositories,
  orders, positions or broker state.
- Inputs such as prompts, history, diffs and context are untrusted and bounded.
- Logs are metadata-first and redact request bodies, model bodies, headers and credentials.

## Executable publication policy

`tests/test_public_documentation.py` scans Markdown and public package metadata. Failure messages emit
only the path and rule name, never the matched value. It requires the root public documents, their
canonical sections and links, plus internal visibility markers for execution-history docs.

Forbidden categories include:

- developer-home absolute paths;
- private repository hostnames and SSH coordinates;
- environment project/issue identifiers and exact internal commit hashes;
- known live model evidence retained from staging history;
- common high-confidence API token formats.

The scan complements existing package inspections and secret discipline; it is intentionally
deterministic and network-free.
