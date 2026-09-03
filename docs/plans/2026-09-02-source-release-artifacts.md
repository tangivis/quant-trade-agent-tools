# Source release artifacts implementation plan

## Objective

Deliver a `0.3.1` release-governance hotfix in which every valid tag retains installable Python and harness
archives, while public registry uploads remain separate opt-in operations with explicit credentials.

## Baseline and protection

- Start `hotfix/source-release-artifacts` from the latest `origin/main` after confirming the previous
  feature branch and worktree are clean.
- Do not stash, reset, clean, rewrite, merge, tag, publish, deploy, or modify a sibling repository.
- Preserve dsh's experimental status and all Intelligence/Product plane boundaries.

## TDD sequence

1. Add static assertions that the tag artifact job always runs, retains all four artifact classes, and
   feeds public jobs.
2. Assert that PyPI and npm rules require their respective explicit enable flag and secret, with a
   disabled fallback.
3. Add a subprocess pack test that reproduces the current `prepublishOnly` Bun/shell failure for pi and
   dsh.
4. Run focused tests and record RED output before changing CI or manifests.
5. Implement the artifact stage, optional publication rules, retained-output publication, and Bash
   lifecycle fix; rerun focused tests to GREEN.
6. Require `0.3.1` in version tests, record RED, then synchronize Python/npm/runtime/locks and rerun GREEN.
7. Update release terminology and operational documentation; keep internal evidence sanitized.
8. Run full tests, typecheck, builds, artifact inspection, secret/path/workspace audits, and diff checks.

## Expected files

- `.gitlab-ci.yml`: artifact stage/job, paths, retention, optional publication rules and dependencies.
- `tests/test_release_metadata.py`: CI, lifecycle, artifact and version contracts.
- `package.json`, `packages/*/package.json`, `pyproject.toml`, runtime identity and locks: `0.3.1`.
- `README.md`, `docs/agent-tools-publish.md`, verification, changelog, handoff and MR draft: public state
  model, evidence, rollout and rollback.
- `openspec/changes/source-release-artifacts/`: proposal, design, spec and task evidence.

## Commit slices

1. `docs(release): specify source artifact governance`
2. `fix(ci): retain opt-in release artifacts`
3. `chore(release): prepare 0.3.1 hotfix`
4. `docs(release): record artifact hotfix verification`

Each slice must be dependency-safe, pass its relevant tests, contain matching specification/evidence, and
be pushed immediately. The final Ready MR targets `main`; no merge, tag or deployment is authorized.

## RED/GREEN evidence

- RED: `uv run pytest tests/test_release_metadata.py -q` produced 3 failed / 7 passed. The old CI had no
  tag artifact job or opt-in publication flags, and both package manifests still used
  `bun run scripts/build.sh`.
- GREEN: the same focused suite produced 10 passed after adding artifact retention, independent
  enable-plus-credential rules, retained-output publication and explicit Bash lifecycle entrypoints.
- Lifecycle refactor check: `npm publish --dry-run` completed `prepublishOnly` for both harness packages,
  called `bash scripts/build.sh`, and retained stable/experimental tag selection without uploading.
- Version RED: Python produced 1 failed / 9 passed and the TypeScript version test produced 1 failed
  because every shipped identity was still `0.3.0`.
- Version GREEN: release metadata plus Gateway capabilities produced 50 Python passed; the TypeScript
  version test produced 1 passed after synchronized `0.3.1` propagation.
- Final full gates: Python 233 passed / 1 opt-in live test skipped; Bun 39 passed / 153 assertions;
  typecheck, pi/dsh builds and Python build passed.
- Strict package audit produced two Python release archives and two npm tarballs at `0.3.1`; extracted
  content contained no credential/auth file, workstation path or workspace-only runtime dependency.
- Documentation RED was 1 failed / 2 passed until the new MR record used the required internal-only
  sanitized marker; focused public/release documentation GREEN was 13 passed.
- Delivery: dependency-safe commits were pushed immediately; the Ready MR targets protected `main` and
  its first complete head pipeline succeeded without enabling auto-merge.
