<!-- visibility: internal-only; sanitized -->

# MR draft: PyPI release activation

## Metadata

- Target: `main`
- Source: `feature/pypi-release-activation`
- Title: `docs(release): activate PyPI publishing status`
- Version: `0.4.0`; no runtime or contract delta.

## Scope

- Replace pending release copy in README and curated Pages with exact `0.4.0` release status.
- Separate GitHub OIDC PyPI identity from internal token fallback and npm credentials.
- Continue to state that npm is unpublished and dsh is experimental.

## Security

- No token, password, provider configuration or environment identifier enters the tree.
- The GitHub PyPI job remains the only job with `id-token: write` and consumes retained build artifacts.
- Release tags remain protected and must point to a commit reachable from public protected main.

## Verification

- RED: 2/2 focused public status tests failed before updating the release copy.
- GREEN: the same 2/2 focused tests pass.
- Full: Python 250 passed / 1 opt-in live case skipped; TypeScript 40 passed; Ruff, typecheck, both harness
  builds, Python build, npm dry-runs, strict OpenSpec, public metadata and security/dependency audits pass.

## Rollout

1. Merge the identical reviewed tree through protected internal and public main.
2. Enable the repository PyPI variable only after Trusted Publisher registration.
3. Create the annotated `v0.4.0` tag on public main and verify build, GitHub Release and PyPI separately.
4. Do not publish npm packages; keep dsh experimental.
