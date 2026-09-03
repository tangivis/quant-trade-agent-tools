# Public Documentation Hardening — Implementation Plan

## Scope

Only modify `quant-trade-agent-tools`. Produce public-grade architecture/security documentation and an
executable, redacted publication-safety gate. Preserve the current branch and dirty worktree; do not
read or modify the sibling repository and do not commit, push, merge, tag or deploy.

## Red -> Green -> Refactor

1. Enumerate repository documentation and public package metadata without printing matched sensitive
   values.
2. Add a failing test requiring root architecture/security documents, README links, canonical plane
   ownership and internal-note visibility markers.
3. Add a deterministic scanner whose failures disclose only file path and rule category.
4. Run the focused test and record missing documents, missing markers and redacted category failures.
5. Add concise root `ARCHITECTURE.md` and `SECURITY.md` using public-safe examples only.
6. Align README, CHANGELOG, detailed architecture and package documentation with the canonical
   ownership and call boundaries.
7. Sanitize handoff, MR draft, verification history and release metadata; retain useful evidence only
   as aggregate, environment-neutral statements.
8. Refactor test allowlists/patterns only to eliminate demonstrated false positives, never to exempt a
   known sensitive value.
9. Run focused/full Python, TypeScript tests/typecheck/build, `uv build`, package inspection,
   publication scan and `git diff --check`.
10. Update OpenSpec tasks, verification, handoff and MR draft with red/green evidence and remaining
    public-release limitations.

## Rollback

Documentation changes are additive or redactions. Rollback should preserve the scanner and canonical
ownership boundaries; environment-specific operational detail belongs outside the repository in an
access-controlled system, not restored to public docs.

## TDD evidence

- Initial focused red: 3 failed. The landing page lacked canonical public terms, execution documents
  lacked the required marker, and the redacted scan reported 20 file/rule violations.
- Packaging red: the sdist allowlist test failed because the two canonical root documents were absent;
  the expanded scan separately identified the remaining historical paths and private remote category.
- Focused green: publication and release-metadata suites passed after documentation redaction, URL
  allowlisting and explicit sdist inclusion.
- Full gates are recorded in `docs/agent-tools-verification.md`; the opt-in network test remained
  disabled.
