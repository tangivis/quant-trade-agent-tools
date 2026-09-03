# Official Harness Adapters

## Why

The repository exposes useful pi and DeepSeek Harness adapters, but their
runtime and lifecycle contracts are not yet aligned with the current host
documentation:

- the shared TypeScript bridge calls `Bun.spawn`, although pi packages may run
  inside the supported Node.js CLI;
- the dsh package mutates arbitrary `ctx["quant.*"]` properties instead of
  registering model-facing tools through the `tools` service;
- the dsh package lacks the current `dsh.bundle` manifest and composition patch
  used by `dsh plugin add`;
- wildcard peer dependencies do not communicate which host APIs were tested.

This leaves local unit tests green while a clean host installation can still
fail before a tool is discovered or invoked.

## What Changes

- Make the shared CLI bridge use Node.js subprocess APIs and accept an
  `AbortSignal`; Bun remains the repository build/test tool, not a published
  adapter runtime requirement.
- Keep the pi package on its documented package manifest and `registerTool`
  extension API while declaring the tested pi compatibility range.
- Replace the experimental dsh consumer shim with a Cordis plugin exporting
  `name`, `inject = ["tools"]`, and `apply(ctx)`.
- Register nine model-facing dsh tools through `ctx.tools.register()` with raw
  JSON Schema inputs, canonical JSON outputs, rendered text, timeouts, and
  cooperative cancellation.
- Publish a dsh bundle manifest plus `cordis.patch.yml` composition layer.
- Keep dsh explicitly experimental until installation, discovery, and real
  tool-call E2E pass against a pinned release.

## Non-Goals

- No changes to the nine canonical business tools or their HTTP mappings.
- No import of `quant_trade`, database access, or local sibling-repository
  dependency.
- No broker execution tools.
- No claim that unit/type/package verification is a real dsh E2E certification.

## Success Criteria

- The CLI bridge runs from a plain Node.js process without a global `Bun`.
- pi still registers exactly nine `quant_*` tools.
- dsh loads through the documented Cordis plugin shape and registers exactly
  nine `quant_*` tools on `ctx.tools`.
- dsh execution forwards the harness cancellation signal to the subprocess.
- npm tarballs contain the built adapter and correct host manifests, but no
  `workspace:*` runtime dependency or local absolute path.
