# Release Readiness Hardening

## Why

The 0.2.0 implementation passes unit tests and builds, but the first artifact
inspection found that the Python source distribution includes the whole
monorepo and that published README metadata contains a developer-specific
absolute path. The GitLab test job also stops before Python package and npm
tarball verification, so a tag can reach publish jobs without exercising the
documented packaging gate.

## What Changes

- Define an explicit Python sdist allowlist for runtime source, tests, license,
  README, changelog, and build metadata, plus Hatch's mandatory VCS metadata.
- Remove developer-specific absolute paths from all published documentation.
- Add automated release metadata tests for local paths, sdist boundaries,
  synchronized versions, and CI packaging gates.
- Make the GitLab test job build and inspect Python and npm release artifacts
  before any tag publish job can start.
- Keep dsh on the `experimental` npm dist-tag until its pinned-host E2E gate is
  completed.

## Non-Goals

- Do not publish packages or create a Git tag as part of this change.
- Do not add credentials to the repository or require live provider keys in CI.
- Do not claim that package inspection replaces pi/dsh clean-host E2E.

## Success Criteria

- Python wheel and sdist contain only declared release inputs, generated
  package metadata, Hatch's mandatory `.gitignore`, and no local absolute path.
- npm dry-run manifests contain only their declared files and no
  `workspace:*` runtime dependency.
- Python, root workspace, pi, dsh, and bridge versions remain synchronized.
- A GitLab tag pipeline cannot enter publish jobs until tests, type checking,
  builds, and artifact inspection have passed.
