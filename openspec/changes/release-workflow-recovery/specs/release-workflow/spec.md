# Release Workflow Recovery Delta

## ADDED Requirements

### Requirement: an immutable tag can be retried safely

The release workflow SHALL support an authorized manual retry for a named existing tag. It SHALL checkout
that tag, prove its commit is reachable from main and require its name to match the package version.

#### Scenario: retry version 0.4.0

- Given `v0.4.0` already exists on public main
- When an operator dispatches release recovery for `v0.4.0`
- Then all tests and archives are rebuilt from that tag
- And the tag ref is not updated or deleted

### Requirement: GitHub Release handling is repository-explicit and idempotent

The release job SHALL pass the repository explicitly to GitHub CLI. An existing release SHALL have its
asset names verified and SHALL NOT be overwritten.

#### Scenario: source release was recovered separately

- Given the GitHub Release already contains every expected archive and checksum
- When the workflow is retried
- Then the GitHub Release job succeeds after asset verification
- And the PyPI job may retry independently with a fresh OIDC identity
