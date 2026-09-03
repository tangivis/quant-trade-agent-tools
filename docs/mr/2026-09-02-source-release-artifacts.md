<!-- visibility: internal-only; sanitized -->

# MR draft: source release artifacts

## Metadata

- Target: `main`
- Source: `hotfix/source-release-artifacts`
- Title: `fix(release): retain source artifacts without registry credentials`
- State: Ready after a successful head pipeline; no auto-merge, tag or deployment.
- Version: `0.3.1`; API contract remains `v1`.

## Why

A prior release tag passed the repository test job but public PyPI/npm attempts were rejected because the
required credential/authorization prerequisites were unavailable. The pipeline conflated a buildable
source revision with public registry publication and did not retain an independent downloadable artifact
set. It also invoked shell scripts through Bun during `prepublishOnly`.

## Changes

- Add a tag-only `source-release-artifacts` job after the full test gate.
- Retain Python sdist/wheel and the pi/dsh npm tarballs without requiring public registry credentials.
- Make PyPI and npm uploads optional: each requires an explicit enable flag and matching protected
  credential; otherwise the job is skipped.
- Publish only the retained archives, avoiding a second build in public jobs.
- Execute pi/dsh shell build scripts through Bash and verify both npm lifecycle dry-runs.
- Synchronize Python, runtime capabilities, root/bridge/pi/dsh metadata and locks at `0.3.1`.
- Document source/artifact release and each public registry as independently observable states.

## Contract and security

- No LLM provider, prompt, product API, DB, Git hosting, repository mutation or trading tool behavior is
  changed.
- The repository and release archives contain no real registry credential, account or scope owner.
- `.npmrc.ci` contains only an environment placeholder and is not packaged.
- Missing enable/credential prerequisites fail closed by skipping public jobs; artifact success is never
  reported as published.
- OIDC/trusted publishing is the recommended follow-up. Protected variables remain the temporary fallback
  only after independent setup and verification.
- dsh remains experimental and uses the experimental npm dist-tag.

## SDD/TDD and verification

```text
CI/lifecycle RED: 3 failed, 7 passed
CI/lifecycle GREEN: 10 passed
version RED: Python 1 failed, 9 passed; TypeScript 1 failed
version GREEN: Python release/capabilities 50 passed; TypeScript 1 passed
full Python: 233 passed, 1 skipped
full Bun: 39 passed, 153 assertions
typecheck/build: passed
artifact audit: two Python archives + two npm tarballs at 0.3.1
security/package audit: passed
```

The skipped Python case is the default-off real-provider smoke. No real provider or public registry
network call is part of the automated test gate. npm publication commands were exercised only with
`--dry-run` to verify lifecycle and dist-tag behavior.

## Rollout

1. Review and merge through protected `main` only after the MR pipeline and discussions pass.
2. In a separately authorized release action, create a version tag from the merged main revision.
3. Confirm the source artifact job retained all four archive classes even when registry variables are
   absent.
4. Treat each public registry as not published unless its explicitly enabled job succeeds.
5. Enable registry publication only after protected credentials or trusted publishing and ownership are
   independently verified.

## Rollback

- Before a tag, revert this hotfix through the normal protected-main MR flow.
- After a tag, retained artifacts and any successfully published registry version are immutable evidence;
  do not rewrite or falsely relabel those states.
- Disable either publication enable flag to keep future public jobs skipped without affecting artifact
  generation.

## Known limitations

- This MR does not configure OIDC/trusted publishing, credentials or registry ownership.
- A real tag pipeline is intentionally outside this MR; static CI contracts and local equivalent package
  builds cover the artifact topology before release authorization.
- dsh still requires pinned-host E2E before it can leave experimental status.
- This MR must not merge, tag, publish or deploy itself.
