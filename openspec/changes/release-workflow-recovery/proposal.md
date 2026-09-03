# Release workflow recovery

## Why

The first public tag proved the build and retained artifacts, but the GitHub Release job lacked explicit
repository context and the PyPI publisher identity needs an external configuration correction. The tag is
immutable, so recovery must rerun the reviewed workflow against that exact tag without moving it.

## What changes

- Give GitHub CLI an explicit repository in the release job.
- Add an operator-only workflow dispatch input for an existing release tag.
- Checkout and validate the selected tag commit rather than the dispatching branch.
- Make GitHub Release creation idempotent while keeping PyPI upload strict.

## Boundaries

- Never update, delete or recreate an existing tag.
- Never use `skip-existing` for PyPI; an unexpected duplicate remains a hard failure.
- Manual recovery still rebuilds and verifies all archives from the immutable tag.
- npm publication remains outside the GitHub workflow.
