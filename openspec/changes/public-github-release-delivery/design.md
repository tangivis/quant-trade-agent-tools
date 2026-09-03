# Design

## Public site

`site/` is an explicit allowlist. A single static HTML document links to the repository, contract and
security policy and explains the two-plane boundary. It contains no analytics, external JavaScript,
provider configuration, runtime coordinates or internal documents. Pages deploys only `site/` after a
push to protected `main`, or a manually authorized dispatch from the default branch.

## Release workflow

The tag workflow first verifies that its commit is reachable from protected `main` and that `vX.Y.Z`
equals the package version, installs from checked-in locks, runs the full credential-free gates, builds
Python sdist/wheel and pi/dsh tarballs, and uploads a single release artifact. A dependent GitHub Release
job downloads those exact files instead of rebuilding them.

PyPI publication is a separate dependent job with `environment: pypi` and `id-token: write`. It runs only
when repository variable `ENABLE_PYPI_PUBLISH` equals `true`; otherwise GitHub source/artifact release can
succeed independently. The PyPA action is pinned to an immutable commit. No password/token input exists.

## Permissions and supply chain

- Workflow defaults are `contents: read`; Pages and GitHub Release jobs receive only their required write
  permission, and PyPI receives only `id-token: write` plus read access.
- Every non-local action reference is a full commit SHA. Repository Actions policy also enforces SHA pins.
- Release builds use GitHub-hosted runners and checked-in Python/Bun locks.
- No pull-request workflow can publish Pages, GitHub Releases or registry packages.

## Rollback

Disable `ENABLE_PYPI_PUBLISH`, remove or correct the trusted publisher from PyPI, and repair workflows
through a reviewed feature PR. Never overwrite an existing version or tag. Pages can be disabled without
affecting packages or runtime services.
