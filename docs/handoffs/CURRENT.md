<!-- visibility: internal-only; sanitized -->

# Current Handoff

## Objective and Git state

- Objective: finish the conversation-context contract and public-release hardening for `0.4.0`.
- Branch: `feature/conversation-context-contract`, based on the immutable `v0.3.1` main revision.
- Active OpenSpec: `openspec/changes/conversation-context-contract/`.
- The internal feature has a passing review pipeline. No merge, tag, registry publication or deployment
  is authorized by this handoff.
- The public GitHub repository exists under the package-aligned name and is intentionally empty while a
  sanitized, reviewed bootstrap path is prepared. Internal historical refs must not be mirrored.

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

## Release state

- Version identity is `0.4.0`; contract version remains `v1`.
- Public package metadata uses the public source repository and current 12-tool descriptions.
- pi and dsh both forward cancellation. dsh remains experimental until pinned-host installation,
  discovery and real tool-call E2E succeed.
- Python and npm registries remain separate, opt-in publication states. Source artifacts do not imply
  public registry availability.

## Remaining delivery steps

- Review the complete diff and commit the acceptance slice through the existing feature MR.
- Bootstrap public delivery without copying internal historical refs. Protect public `main` before normal
  feature PR delivery; do not directly push normal changes to main.

## Full verification

- Python: 242 passed / 1 explicitly gated real-provider case skipped.
- TypeScript: 40 passed; typecheck and both harness bundles passed.
- Ruff, Bandit, Bun audit and resolved Python dependency audit passed.
- Python sdist/wheel and both npm dry-run packages built at `0.4.0`.
- An isolated wheel execution returned `agent-tools 0.4.0`; public documentation and release metadata tests
  passed 15/15.
