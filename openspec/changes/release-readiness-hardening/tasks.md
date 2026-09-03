# Tasks

## 1. SDD

- [x] Record the artifact boundary, CI gate, and dsh release-channel decision.
- [x] Write the multi-file implementation plan.

## 2. TDD: Red

- [x] Add failing tests for the missing sdist allowlist and local paths.
- [x] Add failing tests for synchronized release versions and CI package gates.
- [x] Add a failing test for the MCP server's runtime package version.
- [x] Add a failing assertion that dsh publishes only to `experimental`.
- [x] Add a failing assertion for environment-only npm authentication.
- [x] Add a failing assertion that CI uses the supported Python 3.14 line.
- [x] Add a failing assertion that every CI job exposes mise-managed Bun.

## 3. TDD: Green and Refactor

- [x] Add the minimal Hatch sdist configuration.
- [x] Replace local paths with portable examples.
- [x] Add build and package dry-run checks to the GitLab test job.
- [x] Route dsh tag publishing to the experimental dist-tag.
- [x] Wire npm authentication through a committed variable-only CI config.
- [x] Pin the CI interpreter independently of Runner-global PATH state.
- [x] Add the Bun toolchain path to test and publish jobs.

## 4. Verification

- [x] Run all Python and TypeScript tests and type checking.
- [x] Build Python and both native adapters.
- [x] Inspect Python archives and npm dry-run manifests.
- [x] Run isolated wheel CLI and Gateway smoke tests.
- [x] Check tracked content and artifacts for secrets and local paths.
- [x] Update changelog, release docs, and verification evidence.
