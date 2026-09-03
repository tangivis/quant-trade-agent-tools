<!-- visibility: internal-only; sanitized -->

# Release workflow recovery plan

## Objective

Recover the failed public release jobs without changing the immutable tag or weakening package integrity.

## Sequence

1. Add static failures for missing workflow dispatch, tag-selected checkout and explicit repository context.
2. Add the minimal recovery input and shared release-tag identity.
3. Make an existing GitHub Release an exact asset-verification path, not an overwrite path.
4. Run focused metadata tests, strict OpenSpec and all Python/TypeScript/build/security gates.
5. Deliver through protected internal and public main.
6. Dispatch the existing tag only after PyPI reports a matching Trusted Publisher.

## RED/GREEN evidence

- RED: the focused workflow metadata test failed because no manual tag recovery input existed.
- GREEN: the same focused workflow test passes after the minimal implementation.
- Full GREEN: Python 250 passed / 1 opt-in live case skipped; TypeScript 40 passed; Ruff, typecheck,
  pi/dsh builds, Python build, strict OpenSpec, Bandit and Python/Bun dependency audits passed.
