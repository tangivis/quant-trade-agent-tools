# Design: Release Readiness Hardening

## Distribution Boundary

The Python wheel contains only `agent_tools` runtime modules and generated
metadata. The source distribution is deliberately broader so downstream users
can inspect and test it, but it is limited to:

- `src/agent_tools/`
- `tests/`
- `LICENSE`, `README.md`, `CHANGELOG.md`, and `pyproject.toml`
- `.gitignore`, which Hatch's standard sdist builder always includes and does
  not permit excluding

TypeScript workspaces, CI configuration other than the mandatory VCS ignore
metadata, local migration notes, OpenSpec files, and implementation plans are
repository inputs rather than Python package inputs. Native harness packages
continue to use their existing npm `files` allowlists.

## Automated Gates

A small Python contract test reads release metadata without accessing the
network. It verifies:

1. synchronized versions across all published projects;
2. the explicit sdist allowlist;
3. absence of developer home paths in published text inputs;
4. presence of build and package-inspection commands in the GitLab test job;
5. dsh's experimental publish tag.

The CI job then executes the real builders and `npm pack --dry-run --json`.
This keeps fast metadata failures in the test suite while still validating the
actual packaging tools before tag-only jobs are eligible.

CI sets `UV_PYTHON=3.14` because 3.12 through 3.14 are the declared and tested
release lines. Runner-global PATH entries or prerelease interpreters must not
silently select an unsupported Python version.

## Release Semantics

The Python package and pi adapter use the stable `latest` channel for 0.2.0.
The dsh adapter is published with the `experimental` dist-tag because its
documented clean-profile E2E is still open. Creating a version tag remains a
manual, explicit release action after the feature branch is reviewed and
merged.

GitLab injects `PYPI_TOKEN` and `NPM_TOKEN` as masked protected variables.
The committed `.npmrc.ci` contains only an environment placeholder and is
selected only inside npm publish jobs; no registry credential is persisted in
the repository or release artifact.
