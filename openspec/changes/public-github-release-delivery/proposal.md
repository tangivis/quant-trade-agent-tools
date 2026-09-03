# Public GitHub release delivery

## Why

The public source repository has independent pull-request verification, but it does not yet expose a
curated GitHub Pages site or a tag workflow that retains release archives and can publish to PyPI without
a long-lived token. The repository and package metadata therefore cannot point to a live documentation
site or an existing PyPI project yet.

## What changes

- Add a curated static site containing only public architecture, installation, safety and release-state
  information; do not publish the mixed-visibility `docs/` tree.
- Add a GitHub Pages workflow using immutable official action revisions and least-privilege permissions.
- Add a tag workflow that always verifies and retains Python/npm archives, then creates a GitHub Release.
- Add an opt-in PyPI Trusted Publishing job using OIDC and the protected `pypi` environment. It must stay
  skipped until the repository variable and PyPI publisher registration are both ready.
- Add future Pages/PyPI URLs to package metadata with explicit pending-publication wording in README.

## Out of scope

- Merging the open pull request, creating a tag, publishing a package or deploying a runtime service.
- Receiving or storing a PyPI/npm token.
- Publishing internal handoff, verification, MR or environment-specific documents as Pages content.
- Publishing pi/dsh to npm or claiming dsh stable marketplace status.
