# Specification: source release artifacts

## Requirement: credential-independent tag artifacts

Every semantic-version tag pipeline MUST build and retain the Python sdist/wheel, pi npm tarball, and dsh
npm tarball after the complete test gate, without requiring public registry credentials.

### Scenario: registries are disabled

- GIVEN a valid release tag and no publication credentials
- WHEN the pipeline completes its test and artifact stages
- THEN all four release artifact classes are retained by GitLab
- AND public PyPI/npm jobs are skipped
- AND the release is described only as a source/artifact release

## Requirement: explicit public publication

A public registry job MUST run only when the registry's explicit enable flag equals `true` and the
matching credential is present. Artifact creation MUST NOT claim or imply public publication.

### Scenario: only PyPI is enabled

- GIVEN both the PyPI enable flag and PyPI credential are present
- AND npm publication is not enabled
- WHEN the tag pipeline reaches publication
- THEN the Python job may publish the retained Python artifacts
- AND both npm publication jobs remain skipped

### Scenario: enable flag without credential

- GIVEN a public publication enable flag is true
- AND its credential is absent
- WHEN rules are evaluated
- THEN that publication job is skipped rather than attempted or reported as published

## Requirement: correct npm lifecycle execution

pi and dsh package lifecycle hooks MUST execute their shell build scripts through a shell and MUST produce
inspectable npm tarballs. dsh MUST retain its experimental dist-tag policy.

### Scenario: npm pack invokes prepublishOnly

- WHEN npm performs a dry-run pack for either harness workspace
- THEN the shell build completes without Bun interpreting shell builtins
- AND the expected adapter bundle and public metadata are included

## Requirement: synchronized patch identity

All independently built Python, runtime, workspace, pi, dsh, bridge, and lockfile version identities MUST
report `0.3.1`.
