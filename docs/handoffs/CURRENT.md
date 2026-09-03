<!-- visibility: internal-only; sanitized -->

# Current Handoff

## Objective and Git state

- Objective: finish the conversation-context contract and public-release hardening for `0.4.0`.
- Branch: `feature/conversation-context-contract`, based on the immutable `v0.3.1` main revision.
- Active OpenSpecs: `openspec/changes/conversation-context-contract/` and
  `openspec/changes/public-github-release-delivery/`.
- The internal feature has a passing review pipeline. No merge, tag, registry publication or deployment
  is authorized by this handoff.
- The public GitHub repository uses the package-aligned name. Sanitized `main` and
  `feature/conversation-context-contract` histories plus public PR #1 exist without mirrored internal refs.
- The credential-free, Node 24-native pinned-action public `verify` workflow passed on PR #1 and is a
  required, strict check on protected `main`. Merge, tag, registry publication and deployment remain
  unauthorized.
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

## RED/GREEN evidence

- Acceptance RED: Python 8 failed / 44 passed for system-role context, native analyze, version, metadata
  and lint contracts; TypeScript 3 failed / 14 passed for Pi cancellation, analyze schema and version.
- Focused GREEN: Python 119 passed; TypeScript 27 passed after the minimal implementation.
- Ruff baseline under the selected release rules reported 26 existing failures; the configured fixer
  resolved the applicable import/error/modern-typing findings before the final lint gate.
- Public-delivery RED: 4 failed / 12 passed for missing Pages/release workflows and future public metadata;
  focused GREEN: 16 release metadata tests passed with strict OpenSpec validation.

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

- Obtain review before merging public PR #1. Do not merge, tag, publish or deploy from this handoff.
- Register the pending PyPI Trusted Publisher for this repository, `release.yml` and `pypi` environment,
  then enable publication only after review.

## Full verification

- Python: 246 passed / 1 explicitly gated real-provider case skipped.
- TypeScript: 40 passed; typecheck and both harness bundles passed.
- Ruff, Bandit, Bun audit and resolved Python dependency audit passed.
- Python sdist/wheel and both npm dry-run packages built at `0.4.0`.
- An isolated wheel execution returned `agent-tools 0.4.0`; public documentation and release metadata tests
  passed 19/19.
- GitHub release-equivalent local build produced the current sdist/wheel and two four-file npm archives;
  SHA-256 manifest, Bun/Python dependency audits and Bandit passed.
- Public GitHub `verify` passed all credential-free gates with no action-runtime warning; protected `main`
  requires that check, one approving review and resolved conversations.
- The Pages/release/OIDC delivery head passed both internal and public CI. No workflow was manually
  dispatched and no merge, tag, package publication or Pages deployment occurred.
