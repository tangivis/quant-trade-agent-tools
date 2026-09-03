<!-- visibility: internal-only; sanitized -->

# Current Handoff

## Objective and Git state

- Objective: recover public `0.4.0` registry publication without moving its immutable tag.
- Branch: `feature/release-workflow-recovery`, created from the latest internal `origin/main`.
- Active OpenSpec: `openspec/changes/release-workflow-recovery/`.
- The public tag build and retained artifacts passed. GitHub Release was restored from those checksum-
  verified artifacts; PyPI rejected the valid OIDC token because no publisher matched its exact claims.
- The public GitHub repository uses the package-aligned name. Sanitized `main` and
  `feature/conversation-context-contract` histories plus public PR #1 exist without mirrored internal refs.
- The credential-free, Node 24-native pinned-action public `verify` workflow passed on PR #1 and remains a
  required, strict check on protected `main`. Two valid review threads blocked merge and are addressed by
  the active fix; they must be resolved only after exact tests and CI pass.
- Curated Pages and tag/source/PyPI OIDC delivery are being added to the same still-unmerged public-release
  feature. GitHub Pages workflow mode, repository Homepage and the `pypi` environment exist; the Pages
  deployment and PyPI project are not live yet.

## Current contract

- Gateway chat accepts bounded recent history plus optional caller-owned summary without persistence.
- Caller-derived summaries are JSON-encoded at user privilege; the fixed repository policy is the only
  system message.
- The summary producer uses forced structured output and returns the v1 provenance/warnings envelope.
- Canonical conversation create/context/append tools call protected product REST APIs; the repository has
  no database access.
- Canonical analyze accepts only supported `symbol` and optional `question`, then calls native
  `POST /v1/analyze`. The Gateway obtains authoritative facts from product HTTP APIs.
- Product and Gateway Bearer credentials are separate. No provider key enters a harness schema or browser.
- Gateway chat removes all conversation tools from its internal model registry; only explicit harness
  calls can reach product conversation APIs.
- Gateway chat binds its validated selected symbol as user-role JSON and supplies it only to symbol-scoped
  tool calls that omit `symbol`; explicit values remain unchanged and global feeds remain unscoped.
- Explicit legacy analysis rollback uses the dedicated product `/agent/analyze` client method and cannot
  recurse through canonical native Gateway analyze.

## RED/GREEN evidence

- Release recovery RED: the focused workflow metadata test failed on the missing selected-tag dispatch;
  it passes after adding repository-explicit, immutable-tag recovery.
- PyPI activation RED: 2/2 focused tests failed on stale README/Pages pending status; the same tests pass
  after the minimal public metadata update.

- Acceptance RED: Python 8 failed / 44 passed for system-role context, native analyze, version, metadata
  and lint contracts; TypeScript 3 failed / 14 passed for Pi cancellation, analyze schema and version.
- Focused GREEN: Python 119 passed; TypeScript 27 passed after the minimal implementation.
- Ruff baseline under the selected release rules reported 26 existing failures; the configured fixer
  resolved the applicable import/error/modern-typing findings before the final lint gate.
- Public-delivery RED: 4 failed / 12 passed for missing Pages/release workflows and future public metadata;
  focused GREEN: 16 release metadata tests passed with strict OpenSpec validation.
- Public-review RED: 5/5 focused tests failed for the missing dedicated legacy dispatch and selected-symbol
  binding; the same 5/5 are GREEN after the minimal fix. The related suite is 70/70.

## Release state

- Version identity is `0.4.0`; contract version remains `v1`.
- Public package metadata uses the public source repository and current 12-tool descriptions.
- pi and dsh both forward cancellation. dsh remains experimental until pinned-host installation,
  discovery and real tool-call E2E succeed.
- Python and npm registries remain separate, opt-in publication states. Source artifacts do not imply
  public registry availability.
- Public tags will retain four archive classes and create GitHub Releases without registry credentials.
  PyPI remains explicitly disabled by repository variable until an authorized account registers the OIDC
  publisher and enables it.

## Remaining delivery steps

- Deliver the recovery workflow through protected internal and public main.
- Correct the external publisher fields, dispatch the existing `v0.4.0` tag and verify PyPI. npm remains
  unpublished and the tag must not move.

## Full verification

- Python: 250 passed / 1 explicitly gated real-provider case skipped.
- TypeScript: 40 passed; typecheck and both harness bundles passed.
- Ruff, strict active OpenSpec, public documentation/release metadata tests, Bandit, Bun audit and resolved
  Python dependency audit passed.
- Python sdist/wheel and both npm dry-run packages built at `0.4.0`.
- An isolated wheel execution returned `agent-tools 0.4.0`; public documentation and release metadata tests
  passed 19/19.
- GitHub release-equivalent local build produced the current sdist/wheel and two four-file npm archives;
  SHA-256 manifest, Bun/Python dependency audits and Bandit passed.
- Public GitHub `verify` passed all credential-free gates with no action-runtime warning; protected `main`
  requires that check, one approving review and resolved conversations.
- The Pages/release/OIDC delivery head passed both internal and public CI. No workflow was manually
  dispatched and no merge, tag, package publication or Pages deployment occurred.
