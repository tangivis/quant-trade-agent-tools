<!-- visibility: internal-only; sanitized -->

# Draft MR: Contract v1 Intelligence Producers

Status: **Draft — documentation only; no MR has been created**

## Metadata

- Target: `main`
- Source: `feature/agent-decoupling-delivery`
- Title: `feat(gateway): publish contract v1 intelligence producers and native orchestration`
- Repository: `quant-trade-agent-tools`
- Contract: `agent-gateway-v1`

## Git Flow

- Git hosting project: configured outside repository documentation.
- `main` is the default protected branch; push access is `No one` and force push is disabled.
- Merge method is fast-forward, squash defaults on, successful pipeline and resolved discussions are
  mandatory, and the remote source branch is removed after merge.
- The source branch was created from the latest `origin/main`. The prior feature is its ancestor and
  has an identical committed tree.
- All pre-existing dirty entries were preserved without stash/drop when the delivery branch was
  created. The source branch is pushed; no MR was created by this documentation step.

## Producer-first dependency

This producer MR must be reviewed, merged, released and deployed before the `quant_trade` consumer MR
is enabled against it. The product may prepare and test its consumer first, but must pin the released
`openapi/agent-gateway-v1.json` snapshot and retain degraded-mode behavior until the producer endpoint
and `/v1/capabilities` advertise the required task.

Recommended merge/rollout order:

1. Review the complete uncommitted producer worktree; separate unrelated changes if found.
2. Merge this producer MR to protected `main` through required CI/discussion gates using fast-forward
   merge with the default squash policy.
3. Build/publish and deploy an RC Gateway; verify health, auth, capabilities and required OpenAPI routes.
4. Run cross-repo compatibility and staging checks against that exact RC.
5. Merge/enable the `quant_trade` consumer MR and product-owned persistence/mutation adapters.

## Summary

- Publish provider-neutral REST Gateway contracts for native analyze, chat, four synchronous
  enrichment tasks, stateless wish interpretation and side-effect-free code review/respond.
- Make native analyze the default; retain legacy analyze only as explicit rollback.
- Enforce forced structured outputs, phase/action/score/ID/length boundaries, provenance, warnings and
  the common error envelope.
- Complete producer snapshot/runtime parity, including existing `POST /v1/chat` and
  `GET /v1/capabilities`; the verifier supports both GET and POST without reducing required routes.
- Add an explicit real-provider staging smoke that is network-disabled by default.
- Publish canonical root architecture and security policies for the complete Intelligence Plane and
  independent Product/Data/Domain Plane, with an executable redacted publication-safety gate.

## Contract and security

Published product routes:

- `GET /v1/capabilities`
- `POST /v1/analyze`
- `POST /v1/chat`
- `POST /v1/enrich/headlines/sentiment`
- `POST /v1/enrich/sentiment-summary`
- `POST /v1/narratives/gap`
- `POST /v1/translate`
- `POST /v1/interpret/wish`
- `POST /v1/review/code`
- `POST /v1/review/respond`

Security properties:

- No import of `quant_trade` internal modules and no product DB access.
- No broker order/cancel/live execution capability.
- No GitLab credential/client or issue creation; `quant_trade` alone owns that mutation after a fully
  validated `phase=confirmed` wish.
- Provider keys remain environment-only and are not returned in contracts, logs or staging reports.
- Code-review diffs/context are untrusted data; provider calls, prompts and forced schemas stay in this
  repository. The producer cannot modify a repository or call GitLab/product/database/trading APIs.
- The staging report allowlists provider/model, contract, latency, public phase and validation state;
  it drops base URL, key, prompts/history, model text, provider body and exception messages.
- Public documentation and release metadata are scanned for workstation paths, private networks or
  remotes, environment IDs, exact internal revisions, live provider/model assignments, credential
  value examples and non-allowlisted URLs. Failures disclose only the file and rule category.

## Sanitized real-provider evidence

One explicit post-gate staging run completed with a configured provider and redacted model identity:

| Check | Contract | Latency | Structure |
|---|---|---:|---|
| translation | `agent-gateway-v1` | recorded outside repository | valid |
| wish clarifying | `agent-gateway-v1` | recorded outside repository | valid, phase `clarifying` |
| wish confirming | `agent-gateway-v1` | recorded outside repository | valid, phase `confirming` |

No raw translation, wish reply/payload, prompt, history, base URL, provider response or credential is
included in this evidence.

## Sanitized cross-repo staging evidence

The product repository completed a real isolated staging chain through the HTTPS Gateway, the real
Rust consumer, configured model provider and the product-owned mutation adapter. A temporary test
object was independently confirmed closed by both the product runner and external API verification.

The pinned producer snapshot passed the cross-repo verifier. Product regression gates also passed:
Rust 575 passed / 9 ignored, Python 111 passed, and frontend 507 passed with typecheck passing. This
evidence contains no token, endpoint URL, prompt or model-generated body.

## Verification

- Focused smoke/OpenAPI/Gateway: 41 passed, 1 live test skipped by default.
- Pre-code-review full Python baseline with `RUN_REAL_PROVIDER_E2E=0`: 167 passed, 1 skipped.
- Bun packages: 32 passed, 0 failed, 115 assertions.
- `bun run typecheck`: passed.
- `bun run build && uv build`: passed.
- Wheel contains the staging runner, Gateway runtime and producer OpenAPI snapshot.
- `git diff --check`: passed.
- Targeted GitLab/product mutation, DB, internal import and trading mutation audit: passed.
- Explicit configured-provider staging smoke: passed once after all mock/full/build gates; provider and
  model identity remain outside repository documentation.
- Isolated product E2E through HTTPS Gateway, real Rust consumer, configured provider and product-owned
  mutation: passed; the temporary object was independently confirmed closed.
- Cross-repo verifier: passed. Product gates: Rust 575 passed / 9 ignored, Python 111 passed, frontend
  507 passed and typecheck passed.
- Code-review focused red: 36 failed / 30 passed because service/routes/capabilities/snapshot were
  absent; minimal implementation left only 2 snapshot failures, then exact runtime snapshot parity
  reached 66 passed.
- Full producer Python after code-review implementation: 199 passed, 1 opt-in live test skipped.
- TypeScript after code-review implementation: 32 passed / 0 failed / 115 assertions; typecheck and
  pi/dsh builds passed.
- `uv build` and wheel inspection passed; packaged v1 snapshot contains both review routes and all 10
  required product routes match runtime exactly.
- Focused production boundary audit passed: no sibling import, GitLab/DB/repository/coding-agent or
  trading mutation was introduced by the review producer.
- Public-documentation TDD started at 3 failures plus an independent sdist allowlist failure; focused
  publication/release metadata finished at 10 passed.
- Final full Python: 202 passed and 1 opt-in live test skipped; TypeScript remained 32 passed / 0 failed
  / 115 assertions, with typecheck and both builds passing.
- Artifact inspection confirmed the canonical architecture/security files in the sdist, no current
  workspace absolute path, and four-file npm dry-run allowlists for both harness packages.

## Rollout

1. Deploy the Gateway on loopback behind the approved reverse proxy/auth boundary.
2. Verify `/health`, authenticated `/v1/capabilities`, and the pinned OpenAPI artifact.
3. Confirm active orchestration is native and available modes are native/legacy.
4. Enable product consumers task by task; keep deterministic product behavior operational when the
   Gateway is unavailable.
5. Observe provider latency, structured-response error rate, missing-ID repair and wish phase quality.
6. Keep all provider and GitLab credentials in their owning service environments.

## Rollback

- Set `TRADE_AGENT_ORCHESTRATION_MODE=legacy` to roll analyze back during the one-release window.
- Disable/roll back individual product adapters to degraded behavior; never fall back to a direct
  provider call inside `quant_trade`.
- Redeploy the prior producer package if a contract incompatibility is found.
- Wish interpretation has no producer persistence; disabling it cannot require data migration and must
  prevent product issue creation rather than synthesize success.

## Explicit limitations

- dsh remains **experimental** until fixed-version real harness loading/discovery/invocation E2E passes.
- Shadow orchestration is not implemented and is not advertised.
- Durable enrichment claim/result APIs and worker are not implemented.
- Legacy analyze remains for one rollback release and requires a later two-repository retirement change.
- The real-provider smoke currently records one provider family only; other provider presets remain covered by
  provider resolution and mock contract tests, not live staging evidence.

## Reviewer checklist

- [ ] Confirm producer-first merge/release order with the `quant_trade` MR owner.
- [x] Confirm protected-main Git Flow and the new source branch metadata.
- [x] Confirm all required snapshot routes remain present and runtime-compatible through the cross-repo
  verifier.
- [x] Confirm the isolated real product staging chain and product-owned mutation boundary.
- [ ] Review forced schemas, phase/action/score validation and error normalization.
- [x] Review code-review request/output bounds, untrusted-input handling and no-side-effect boundary.
- [ ] Verify package contents and secret/mutation audit output in CI.
- [ ] Confirm rollout monitoring and legacy rollback owner/window.
- [ ] Do not mark dsh stable or advertise shadow/durable worker in this MR.
