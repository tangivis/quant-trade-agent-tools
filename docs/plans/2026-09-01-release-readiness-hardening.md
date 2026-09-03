# Release Readiness Hardening Plan

## Objective

Turn the locally green 0.2.0 working tree into a reproducible release candidate
whose Python and npm artifacts are inspected by the same GitLab pipeline that
guards tag publishing.

## TDD Sequence

1. Add metadata tests that fail on the current implicit sdist contents, local
   absolute paths, missing CI artifact checks, and dsh's incorrect stable tag.
2. Add only the Hatch allowlist, portable docs, CI commands, and dsh dist-tag
   needed to satisfy those contracts.
3. Refactor duplicated package checks only if the green implementation shows a
   maintenance issue.
4. Run the full repository verification matrix and isolated installation
   smoke tests.

## Files and Ownership

- `pyproject.toml`: Python sdist boundary.
- `tests/test_release_metadata.py`: release metadata contracts.
- `.gitlab-ci.yml`: pre-publish artifact gates and release tags.
- `README.md`, migration/publish/verification docs, `CHANGELOG.md`: portable
  installation examples and current evidence.
- npm manifests and scripts: published version and dist-tag behavior.

## Exit Criteria

- All prescribed repository commands pass.
- Built archives match their allowlists and contain no local absolute paths,
  secrets, or runtime `workspace:*` dependencies.
- The feature branch is ready to push and open as an MR.
- Remote release remains blocked until an online GitLab Runner and protected
  package credentials are available.
