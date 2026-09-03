# Official Harness Adapters Implementation Plan

## Objective

Align pi and DeepSeek Harness integrations with their documented extension,
tool lifecycle, and package distribution APIs while preserving the stable
CLI/MCP boundary and the repository's HTTP-only relationship with
`quant_trade`.

## Files and Ownership

- `packages/cli-bridge/`: Node-compatible spawn and cancellation contract.
- `packages/agent-tools-pi/`: tested peer range and unchanged native extension.
- `packages/agent-tools-dsh/`: official Cordis plugin, tool registry, bundle
  patch, package metadata, build externalization, and tests.
- `README.md`, package READMEs, publish/architecture/verification docs, and
  `CHANGELOG.md`: installation dependencies, maturity, and evidence.
- `openspec/changes/official-harness-adapters/`: requirements and task record.

## TDD Sequence

1. Add bridge tests that fail while `spawn.ts` uses `Bun.env`/`Bun.spawn` and
   does not accept a caller signal.
2. Add dsh tests that fail while the module lacks `name`, `inject`, `apply`,
   `ctx.tools.register`, canonical outputs, and signal forwarding.
3. Add package tests that fail while peers are wildcarded and the dsh bundle
   manifest/patch are absent.
4. Replace only the subprocess boundary with Node.js APIs; keep CLI arguments,
   timeouts, stdout/stderr parsing, and error semantics stable.
5. Replace the dsh shim with the current official plugin/tool shape and keep it
   a thin CLI adapter.
6. Build bundles, execute the bridge under plain Node.js, and inspect npm
   tarballs before updating verification evidence.

## Verification Gates

- `bun test packages/`
- `bun run typecheck`
- `bun run build`
- plain `node` import/invocation of the built bridge code
- `uv run pytest tests/ -v`
- `uv build`
- `npm pack --dry-run --json` for pi and dsh
- tarballs contain no secret, `workspace:*` runtime dependency, sibling
  repository path, or local absolute path

## Compatibility Decisions

- pi targets the currently tested `0.84.x` host API line.
- dsh targets one explicitly recorded prerelease tool API line and remains
  experimental.
- MCP remains the preferred integration for untested or future harnesses.
- dsh stability still requires a separate clean-profile E2E against a pinned
  dsh release; this implementation does not waive that gate.
