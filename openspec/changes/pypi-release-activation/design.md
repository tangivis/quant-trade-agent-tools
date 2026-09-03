# Design

## Public status contract

README and the curated Pages site identify `0.4.0` as the current release and link to its GitHub Release
and PyPI project. They must not claim npm publication or stable dsh support.

## Publication identity

The GitHub release workflow keeps `contents: read` globally and grants `id-token: write` only to the
dedicated `pypi-publish` job. That job consumes the build artifact and is enabled by the repository
variable only after the external Trusted Publisher registration exists. No PyPI token is stored.

Internal GitLab and npm publishing retain their separately documented credential gates; describing the
public OIDC path must not weaken those controls.

## Delivery

The documentation delta follows the normal protected internal and public pull-request flow. After both
main branches contain the identical reviewed tree, the public repository enable variable is set and an
annotated `v0.4.0` tag is created on public main. Workflow and registry results are verified independently.
