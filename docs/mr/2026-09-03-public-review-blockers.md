<!-- visibility: internal-only; sanitized -->

# MR draft: public review blockers

## Metadata

- Target: `main`
- Source: `feature/public-review-blockers`
- Title: `fix(gateway): preserve legacy and symbol boundaries`
- Version: `0.4.0`; Gateway contract remains `v1`.

## Scope

- Route explicit legacy analysis rollback through a dedicated product client method.
- Carry the validated Gateway chat symbol as user-role JSON.
- Default omitted symbol arguments only for the canonical symbol-scoped tool allowlist.
- Preserve explicit tool symbols and leave global news/sentiment calls unscoped.

## Security and compatibility

- No REST or OpenAPI request/response schema changes.
- No database, Git hosting, repository, order, cancel or broker mutation.
- Invalid symbols still fail closed before model or product calls.
- Standalone agent calls remain compatible because selected-symbol context is optional.

## TDD evidence

- RED: five focused failures covered the absent legacy method, wrong provider dispatch, dropped Gateway
  symbol and missing runtime binding.
- GREEN: the same five tests pass; the broader client/Gateway/runtime/tool suite also passes after its
  legacy fake adopts the dedicated protocol.
- Full: Python 249 passed / 1 opt-in live case skipped; TypeScript 40 passed; Ruff, typecheck, both harness
  builds, Python packages, strict OpenSpec, public-doc/release metadata and security/dependency audits pass.

## Rollout and rollback

- Merge through protected internal and public main only after their required pipelines and conversations
  pass.
- Roll back with a new protected-main change. Do not rewrite release tags.
- Public package publication remains separately disabled pending external registry trust configuration.
