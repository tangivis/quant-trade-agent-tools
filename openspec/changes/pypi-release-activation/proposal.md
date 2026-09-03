# PyPI release activation

## Why

The public Trusted Publisher is now registered, but the release candidate documentation still describes
PyPI and Pages as pending. Publishing the immutable `v0.4.0` tag with those statements would make the
release artifacts immediately stale.

## What changes

- Change public status copy from pending/release-candidate language to the exact `0.4.0` release state.
- Clarify that the public GitHub OIDC path needs no stored PyPI token or PyPI review queue.
- Preserve the independently gated npm and internal GitLab token-based publication paths.
- Verify public release metadata before enabling the repository publication flag and tagging public main.

## Boundaries

- No runtime, API contract, provider, model, database or trading behavior changes.
- No credential values are added to source, workflow inputs or artifacts.
- The immutable release tag is created only after protected-main delivery and all release gates pass.
