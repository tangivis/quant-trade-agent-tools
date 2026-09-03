<!-- visibility: internal-only; sanitized -->

# MR draft: release workflow recovery

## Metadata

- Target: `main`
- Source: `feature/release-workflow-recovery`
- Title: `fix(release): recover immutable tag publishing`
- Version: `0.4.0`; release automation only.

## Scope

- Add an operator-only existing-tag workflow dispatch.
- Checkout and verify the selected tag rather than the dispatch branch.
- Pass explicit repository context to GitHub CLI.
- Treat an existing GitHub Release as an exact asset verification path without overwrite.

## Security

- The tag remains immutable and must be reachable from protected public main.
- PyPI upload remains strict, tokenless and isolated to the `pypi` environment.
- No npm publication, long-lived credential or artifact overwrite is introduced.

## Verification

- RED: release metadata test failed on the absent recovery contract.
- GREEN: the focused workflow recovery test passes.
- Full: Python 250 passed / 1 opt-in live case skipped; TypeScript 40 passed; Ruff, typecheck, builds,
  strict OpenSpec and security/dependency audits pass.

## Recovery

After external PyPI publisher fields match, dispatch `Release` with the existing tag. Verify the GitHub
Release, PyPI JSON metadata and archives independently; do not move the tag.
