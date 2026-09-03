# PyPI Release Activation Delta

## ADDED Requirements

### Requirement: public release status is exact

Public README and Pages content SHALL identify the current tagged release and SHALL link separately to
the GitHub Release and PyPI project. They SHALL continue to mark dsh experimental and SHALL NOT imply npm
publication.

#### Scenario: visitor inspects version 0.4.0

- Given the Trusted Publisher is registered and the release tag is authorized
- When the reviewed release tree is published
- Then README and Pages identify `0.4.0` as released
- And installation points to the public PyPI project

### Requirement: public PyPI publication is tokenless

The GitHub PyPI job SHALL use OIDC with a dedicated environment and SHALL NOT require or read a stored
PyPI token. Internal GitLab and npm jobs SHALL retain their independent credential conditions.

#### Scenario: public tag workflow publishes Python archives

- Given the repository enable variable is true and the trusted identity matches
- When a valid main-ancestry tag runs the release workflow
- Then only the PyPI job receives `id-token: write`
- And no long-lived PyPI credential is present
