<!-- visibility: internal-only; sanitized -->

# PyPI release activation plan

## Objective

Publish `0.4.0` through the registered tokenless PyPI identity without shipping stale public status copy
or changing runtime and contract behavior.

## Sequence

1. Add failing tests for exact released status and separate OIDC versus credential-based paths.
2. Update only public status, publication guidance and delivery evidence.
3. Run focused metadata tests, strict OpenSpec and complete Python/TypeScript/build/security gates.
4. Deliver the identical tree through protected internal and public review branches.
5. Enable the GitHub publication variable, tag public main and observe build, GitHub Release and PyPI jobs.
6. Verify public artifacts and package metadata; leave npm unpublished and dsh experimental.

## RED/GREEN evidence

- RED: 2/2 focused tests failed because README and the curated Pages site still identified PyPI and
  `0.4.0` as pending.
- GREEN: the same 2/2 focused tests pass after the minimal documentation update.
- Full GREEN: Python 250 passed / 1 opt-in live case skipped; TypeScript 40 passed; Ruff, typecheck,
  pi/dsh builds, Python build, npm dry-runs, strict OpenSpec, public documentation/release metadata,
  Bandit and Python/Bun dependency audits passed.
