# Security

## Security model

`quant-trade-agent-tools` is an Intelligence Plane that processes bounded product facts and user text
through configured model providers. It is not a broker, product database, Git hosting client or
repository automation service. Model output is decision support and never authorizes execution.

The independent Product/Data/Domain Plane (`quant_trade`) owns product identity, persistence,
deterministic risk and execution policy, and any product-approved external mutation.

## Trust boundaries

- Treat every REST, MCP and CLI input as untrusted.
- Treat prompts embedded in history, diffs, headlines and context as data, not system instructions.
- Never promote a caller-supplied or model-generated conversation summary to the system role.
- Do not expose product-owned conversation tools inside the Gateway chat agent loop; harness users invoke
  those tools explicitly under product authorization.
- Validate model output with exact schemas, enums, length bounds and unknown-field rejection.
- Fail explicitly on provider, transport, contract or context errors.
- Do not convert failures into fabricated successful analysis or approval.

## Credential management

- Provider credentials belong only in Intelligence Plane deployment secret storage.
- Product, database, Git hosting and broker credentials do not belong in this repository or runtime.
- Credentials must never appear in source, committed environment files, documentation examples,
  request/response bodies, browser state, build artifacts or test fixtures.
- `.env.example` documents variable names with empty or unmistakably non-secret placeholders only.
- Rotate a credential immediately if it may have entered a log, artifact, issue or commit history.

## Privacy and data minimization

The Gateway should receive only fields required by the selected versioned contract. Callers should
remove unrelated source code, personal data, proprietary text and secrets before submitting prompts,
history, diffs or context.

The Intelligence Plane is stateless for chat, wish interpretation and code-review endpoints unless a
future versioned contract explicitly states otherwise. It does not persist product records or access the
product database. Provider-side retention is deployment-specific and must be reviewed by operators
before enabling a provider for sensitive workloads.

## Logging and observability

Safe operational logs are metadata-first: request ID, route, timing, provider category, model category,
tool name and normalized error code. By default, do not log:

- authorization headers or environment values;
- prompt, history, diff, context or full tool arguments;
- raw model requests/responses or provider error bodies;
- product records, cookies or user identifiers.

Diagnostic logging must preserve the same redaction rules and be disabled after the investigation.

## Prohibited side effects

The Intelligence Plane must not directly:

- connect to or mutate the product database;
- create, edit, approve or close Git hosting objects;
- checkout, edit, commit, push or merge a product repository;
- place, change or cancel orders or modify broker positions;
- expose a generic mutation tool that bypasses Product/Data/Domain Plane policy.

Code review/respond returns text and a bounded verdict only. Wish interpretation returns validated
intent only. Any later product-approved action belongs to the Product/Data/Domain Plane.

## Network and deployment controls

- Bind internal services according to the operator's network policy and place public access behind an
  authenticated reverse proxy.
- Apply request-size limits, timeouts and rate limits at both proxy and application boundaries.
- Restrict outbound access to approved product APIs and model endpoints.
- Keep browser clients on the product boundary; do not expose provider credentials or internal service
  topology.
- Maintain deterministic degraded behavior when the Intelligence Plane is unavailable.

## Supply-chain and release controls

- Use the repository's locked Python and TypeScript toolchains.
- Run tests, type checks, builds, artifact inspection and publication-safety scanning before release.
- Public pull-request CI uses read-only repository permissions and immutable action revisions. It must not
  receive provider or registry credentials and cannot enable opt-in live-provider or publication jobs.
- Review packaged files for local paths, credentials and workspace-only runtime dependencies.
- Keep the default branch protected and merge through reviewed, passing pipelines.
- Keep experimental harness adapters clearly marked until their pinned end-to-end gates pass.

## Vulnerability reporting

Report suspected vulnerabilities through the maintainers' private security-reporting channel. Include a
minimal reproduction, affected version, impact and suggested mitigation when possible. Do not include
credentials, proprietary datasets, private prompts or live exploit data in a public issue.

If no private channel is visible in the distribution metadata, contact the maintainers through the
hosting platform and request a private reporting path before sharing details.

## Supported boundary

Security fixes are applied to supported releases and the current development branch. Deployment owners
remain responsible for provider terms, data residency, authentication, network isolation, secret
rotation and product-side execution policy.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete plane and interface model.
