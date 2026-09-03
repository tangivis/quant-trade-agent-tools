<!-- visibility: internal-only; sanitized -->

# Public GitHub release delivery plan

## Objective

Prepare the public repository for a curated Pages site, credential-independent GitHub source releases and
tokenless opt-in PyPI publication while preserving protected-main review and the existing runtime boundary.

## TDD sequence

1. Add static tests that fail because the site and two workflows do not exist.
2. Add the minimal public page and Pages workflow with pinned official actions and scoped permissions.
3. Add the tag build/release workflow, exact version check, retained archives and opt-in OIDC publisher.
4. Update package URLs and public/internal delivery documentation.
5. Run strict OpenSpec, focused tests, then all Python/TypeScript/lint/typecheck/build/package gates.
6. Scan the site, workflows, archives, diff and reachable public history for sensitive identifiers.
7. Push conventional commits to the existing unmerged public-release feature and wait for both pipelines.

## External completion boundary

An authorized PyPI account must register the pending Trusted Publisher for the public repository,
`release.yml` workflow and `pypi` environment. A separate GitHub reviewer must approve the public PR.
Neither step requires sharing a credential with this repository or an agent.

## RED/GREEN evidence

- RED: `tests/test_release_metadata.py` reported 4 failed / 12 passed because Pages, release workflow and
  future public URL metadata did not exist.
- Integrity RED: the first workflow omitted a release checksum manifest; the focused checksum assertion
  failed until all Python/npm archives and `SHA256SUMS` shared one retained artifact.
- Focused GREEN: all 16 release metadata tests passed and the OpenSpec delta passed strict validation.
- Full GREEN: Python 246 passed / 1 opt-in real-provider case skipped; TypeScript 40 passed; Ruff,
  typecheck, both bundles, Python build, four-file npm archive inspection, SHA-256 manifest, Bun audit,
  resolved Python dependency audit and Bandit passed.
- Remote GREEN: the internal and public PR pipelines passed. Pages workflow mode, repository Homepage and
  the empty `pypi` environment were configured; `ENABLE_PYPI_PUBLISH` remains false, so nothing was
  deployed or published.
