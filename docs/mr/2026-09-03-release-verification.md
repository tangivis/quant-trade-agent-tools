<!-- visibility: internal-only; sanitized -->

# MR draft: record 0.4.0 release verification

## Metadata

- Target: `main`
- Source: `feature/release-verification`
- Title: `docs(release): record 0.4.0 publication`

## Evidence

- The protected tag was not moved during recovery.
- GitHub Release contains Python wheel/sdist, pi/dsh tarballs and the checksum manifest.
- Recovery build, exact existing-release verification and PyPI OIDC publication passed.
- PyPI metadata exposes `0.4.0`, one non-yanked wheel and one non-yanked sdist.
- Fresh-cache installation reports `agent-tools 0.4.0`.

## Boundaries

- No token, provider configuration, internal environment identifier or model content is recorded.
- npm packages are not claimed as published and dsh remains experimental.
- This change records evidence only; it does not change runtime, contract, tag or artifacts.
