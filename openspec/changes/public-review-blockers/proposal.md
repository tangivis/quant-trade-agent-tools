# Public review blockers

## Why

The protected public pull request surfaced two valid release blockers after the initial delivery merge:
the explicit legacy analysis rollback still calls the newly native, keyword-only client method, and Gateway
chat does not bind its validated selected symbol to model context or omitted tool arguments. Both can cause
an explicit runtime failure or cross-symbol data selection despite passing existing fake-based tests.

## What changes

- Add a dedicated product-legacy analysis client method and route only `LegacyAnalysisProvider` through it.
- Pass the validated chat symbol into the agent as untrusted request context.
- Inject that symbol when a model omits `symbol` for a symbol-scoped canonical tool; preserve an explicit
  valid tool argument and never add symbol scoping to global news/sentiment.
- Add exact client, provider, agent-runtime and Gateway service regression tests.

## Boundaries

- Canonical analyze remains native `POST /v1/analyze`; legacy product analysis remains explicit rollback.
- No database, Git hosting, repository or broker mutation is added.
- Invalid symbols still fail before a model or product HTTP call.
