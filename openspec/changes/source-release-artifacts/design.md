# Design: source release artifacts

## State model

A release has two explicit states:

1. **Source/artifact release** — a versioned Git tag passed the full repository gate and GitLab retained
   the Python sdist/wheel and both npm tarballs. This state requires no public registry credential.
2. **Public registry publication** — one or more retained artifacts were uploaded to PyPI or npm by an
   explicitly enabled credentialed job. Each registry is an independent state; artifact success never
   implies publication success.

Documentation and CI output must use these terms instead of treating a successful tag or artifact build
as proof that a public package exists.

## Pipeline topology

```text
tag vX.Y.Z -> test -> source-release-artifacts -> optional registry jobs
```

The test job remains the complete quality gate and checks tag/version identity. The artifact job runs on
every semantic-version tag after that gate, creates `dist/*.tar.gz`, `dist/*.whl`, and two npm `.tgz`
archives in a dedicated directory, then uploads those paths using GitLab `artifacts`. Its output is the
input to public publication jobs via `needs` artifacts, preventing a second untracked build.

PyPI publication requires both `ENABLE_PYPI_PUBLISH == "true"` and `PYPI_TOKEN`. npm publication requires
both `ENABLE_NPM_PUBLISH == "true"` and `NPM_TOKEN`; pi uses the stable npm tag while dsh remains
`experimental`. A final `when: never` rule makes the disabled state explicit. Credentials remain external
to artifacts and source control.

Longer term, registry-native OIDC/trusted publishing is preferred because it removes long-lived upload
tokens. Until configured and tested, masked/protected CI variables are the supported fallback.

## npm lifecycle

The package `build` scripts call `bash scripts/build.sh`. `prepublishOnly` may invoke that script through
the package manager, but Bun is never asked to parse the shell file as a Bun script. A subprocess test
runs `npm pack --dry-run` for both workspaces and asserts successful lifecycle execution and expected
archive contents.

## Verification and security

- Parse the CI file in static tests and assert tag artifacts, retention paths, job dependencies, and
  enable-plus-secret rules.
- Inspect all synchronized version sources.
- Build and inspect all four artifact types.
- Scan tracked/release files and archives for secrets, workstation paths, `.env`, registry auth files,
  and workspace-only runtime dependencies.

## Rollback

Revert the hotfix commit before creating a new tag. Existing retained artifacts and already published
registry versions are immutable external evidence and must not be described as rolled back or deleted.
