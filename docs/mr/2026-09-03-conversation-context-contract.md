<!-- visibility: internal-only; sanitized -->

# MR draft: conversation context and public release hardening

## Metadata

- Target: `main`
- Source: `feature/conversation-context-contract`
- Title: `feat(context): add safe shared conversation contracts`
- Version: `0.4.0`; Gateway contract remains `v1`.

## Scope

- Add stateless conversation summary input/output contracts and three product-owned conversation tools.
- Support both declared symbols through Gateway chat/analyze context collection.
- Keep caller-derived summaries at user privilege and preserve the fixed system policy boundary.
- Correct canonical analyze to call native Gateway `/v1/analyze` with only symbol/question.
- Forward cancellation in both pi and dsh adapters.
- Add public source metadata, accurate 12-tool descriptions and a Python lint gate.
- Add a credential-free public GitHub CI gate with immutable action revisions, read-only permissions and
  no provider or registry secrets.
- Add a curated Pages site plus tag-retained GitHub Releases and independently gated, tokenless PyPI OIDC
  publication.

## Contract and security

- Product conversation ownership, storage, retention and authorization remain outside this repository.
- The Intelligence Plane owns provider credentials, prompts and structured model execution.
- Product and Gateway credentials are separately injected and never included in public metadata or
  archives.
- The tools do not import product internals, access a database, mutate Git hosting or execute broker
  actions.
- Public delivery must not mirror internal historical refs or execution documents.

## Verification

```text
acceptance RED: Python 8 failed / 44 passed; TypeScript 3 failed / 14 passed
focused GREEN: Python 119 passed; TypeScript 27 passed
full Python: 246 passed / 1 opt-in live case skipped
full TypeScript: 40 passed
Ruff/typecheck/build/wheel isolated smoke/npm dry-run/security audits: passed
public CI static contract: RED missing workflow and legacy Node action revisions; GREEN 13 release metadata
tests passed
public GitHub PR verify: passed without action-runtime warnings; protected main requires this strict check
public delivery RED/GREEN: 4 failed / 12 passed before implementation; 16 release metadata tests passed
release-equivalent archives/checksums and Bun/pip/Bandit audits: passed
```

## Rollout and rollback

1. Merge only through protected internal main after pipeline and discussions pass.
2. Bootstrap the empty public repository from a sanitized reviewed snapshot, not an internal mirror.
3. Require the successful public `verify` check on protected `main` before review merge.
4. Publish source artifacts independently from optional PyPI/npm registry jobs.
5. Keep GitHub PyPI publication disabled until the external Trusted Publisher registration matches
   `release.yml` and the `pypi` environment.
6. Keep dsh on the experimental distribution tag.
7. Roll back through a new protected-main MR; never rewrite an existing tag or claim skipped registry jobs
   as published.

## Known limitations

- dsh still requires pinned-host E2E before stable marketplace positioning.
- Users need compatible product and Intelligence Gateway HTTP services; adapters do not embed those
  services.
- Public trusted publishing and registry ownership are separate follow-up configuration steps.
