# Tasks: source release artifacts

## 1. SDD

- [x] Define independent source/artifact and public registry publication states.
- [x] Define credential-independent artifact retention and fail-closed publication rules.
- [x] Define npm lifecycle, security, rollback, and `0.3.1` version boundaries.

## 2. RED

- [x] Add static CI tests for retained tag artifacts and explicit enable-plus-credential publication.
- [x] Add a package lifecycle test reproducing the Bun/shell `prepublishOnly` failure.
- [x] Change version contract tests to require `0.3.1` before metadata is bumped.
- [x] Record focused failing evidence in the implementation plan.

## 3. GREEN and refactor

- [x] Add the tag artifact job and consume its retained outputs from optional publish jobs.
- [x] Gate PyPI/npm jobs independently behind explicit enable flags and matching credentials.
- [x] Execute harness shell build scripts with Bash during package lifecycle.
- [x] Propagate `0.3.1` through Python, runtime, npm manifests, and locks.
- [x] Refactor CI naming and documentation so no state implies false publication.

## 4. Verification and delivery

- [x] Run focused and full Python/TypeScript tests, typecheck, builds, and package inspection.
- [x] Audit tracked files and artifacts for credentials, local paths, auth files, and workspace runtime links.
- [x] Update README, publish guide, verification, changelog, handoff, and MR draft.
- [x] Make dependency-safe conventional commits and push each immediately.
- [x] Create a Ready MR targeting protected `main` and wait for a successful pipeline.
- [x] Do not merge, tag, publish, or deploy.
