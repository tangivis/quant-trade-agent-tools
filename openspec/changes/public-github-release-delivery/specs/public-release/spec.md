# Public Release Delta

## ADDED Requirements

### Requirement: curated public documentation site

The repository SHALL publish only the explicit `site/` directory to GitHub Pages after protected `main`
changes. The site SHALL describe the product boundary, installation and release state without exposing
internal execution documents or sensitive configuration.

#### Scenario: Pages deployment

- Given a reviewed change has merged to public `main`
- When the Pages workflow runs
- Then it uploads only `site/`
- And it uses pinned official actions with read-only source access and Pages-specific deployment permission

### Requirement: credential-independent source release

A valid version tag SHALL always run full verification, build Python and harness archives, retain them as
workflow artifacts, and attach the same archives to a GitHub Release without registry credentials.

#### Scenario: no registry publisher is configured

- Given `ENABLE_PYPI_PUBLISH` is absent or false
- When a valid version tag is pushed
- Then tests, builds and GitHub source/artifact release can succeed
- And the PyPI job is skipped without claiming publication

### Requirement: tokenless opt-in PyPI publication

PyPI publication SHALL use OIDC Trusted Publishing through the `pypi` environment and SHALL NOT accept a
stored username, password or API token.

#### Scenario: trusted publisher is enabled

- Given the PyPI project trusts this repository, workflow and environment
- And `ENABLE_PYPI_PUBLISH` equals true
- When a validated version tag completes the build job
- Then the pinned PyPA publisher uploads the previously built distributions with `id-token: write`
