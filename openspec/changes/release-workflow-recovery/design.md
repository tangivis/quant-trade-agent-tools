# Design

## Selected release identity

`RELEASE_TAG` resolves to the required workflow-dispatch input for a manual run and to `github.ref_name`
for a tag push. Checkout uses the same selection. The build verifies that checked-out `HEAD` is reachable
from public main and that `RELEASE_TAG` exactly matches the synchronized package version.

## Idempotent source release

The GitHub Release command always receives `--repo "$GITHUB_REPOSITORY"`, so it does not depend on a
checkout in its isolated job. If the release already exists, the job verifies the exact expected asset
names instead of attempting to create or replace it. It never overwrites release assets.

## PyPI recovery

After the external publisher fields match, an authorized operator dispatches `release.yml` with the
existing tag. The workflow rebuilds that tag from scratch and the PyPI job exchanges a fresh OIDC token.
The build artifacts, GitHub Release and PyPI project remain independently observable.
