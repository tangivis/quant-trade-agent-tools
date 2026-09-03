# Release Artifacts Specification

## Requirement: Explicit Python distribution boundary

The Python source distribution MUST use an explicit allowlist and MUST NOT
contain TypeScript workspaces, CI configuration beyond Hatch's mandatory VCS
ignore metadata, local plans, or developer home paths.

### Scenario: Build release archives

- WHEN `uv build` creates the wheel and source distribution
- THEN the wheel contains only Python runtime modules and package metadata
- AND the source distribution contains only declared Python release inputs
- AND neither archive contains a developer-specific absolute path

## Requirement: Synchronized published versions

All independently published artifacts MUST use the same semantic version.

### Scenario: Validate manifests

- WHEN release metadata tests read `pyproject.toml` and npm manifests
- THEN Python, root, pi, dsh, and bridge versions are identical
- AND the MCP server reports the Python package version rather than a separate
  hard-coded value

## Requirement: Tag pipeline packaging gate

Tag-only publish jobs MUST depend on a test job that builds and inspects all
release artifacts.

### Scenario: Run a tag pipeline

- WHEN a `vX.Y.Z` tag pipeline is created
- THEN tests, type checking, builds, Python archive inspection, and npm pack
  dry-runs complete before publish jobs become eligible
- AND the dsh package is published using the `experimental` dist-tag
