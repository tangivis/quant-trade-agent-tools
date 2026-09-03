# Design: Official Harness Adapters

## Compatibility Surfaces

MCP and the Python CLI remain the stable core. Native adapters contain only
host registration, argument serialization, subprocess lifecycle, and result
projection.

```text
pi ExtensionAPI.registerTool ─┐
                              ├─> Node-compatible CLI bridge
dsh ctx.tools.register ───────┘          │
                                         └─> uvx quant-trade-agent-tools
                                                   │
                                                   └─> quant_trade HTTP API
```

Neither adapter resolves a `../quant_trade` checkout. The only `quant_trade`
runtime dependency is the published HTTP contract configured by
`QUANT_TRADE_API_URL` and `QUANT_TRADE_AGENT_URL`.

## Node-Compatible CLI Bridge

`packages/cli-bridge` uses `node:child_process` rather than the Bun global.
The default command stays:

```text
uvx quant-trade-agent-tools <subcommand> [...args]
```

`AGENT_TOOLS_PYTHON_CMD` remains the local-development override. The bridge
captures stdout/stderr, maps timeout to exit code 124, maps cancellation to a
non-zero result, and waits for the child process to settle. An optional caller
`AbortSignal` lets a harness cancel work it owns.

## pi Adapter

The pi adapter keeps the host's documented form:

- a `pi.extensions` entry in `package.json`;
- a default extension factory;
- one `pi.registerTool()` call per canonical tool.

The host package is a peer dependency because pi owns its lifecycle. The peer
range is limited to the minor line used for verification instead of `*`.

## DeepSeek Harness Adapter

The dsh package follows the documented Cordis plugin lifecycle:

```ts
export const inject = ["tools"];
export function apply(ctx: Context) {
  ctx.tools.register(toolDefinition);
}
```

Each definition contains:

- a stable `quant_<canonical-name>` model-facing name;
- the shared canonical JSON Schema as `parameters`;
- an object-valued output contract and deterministic text renderer;
- an executor that delegates to the shared CLI bridge;
- the canonical tool timeout;
- propagation of `exec.signal` to the child process.

Raw JSON Schema definitions are appropriate at this adapter boundary because
the schemas originate from the cross-harness canonical snapshot. The dsh
registry owns validation and lifecycle disposal.

## dsh Distribution

The npm package declares:

```json
{
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

The patch inserts the package by npm name. Host runtime packages remain peer
dependencies and are external to the adapter bundle. The tested prerelease
line is pinned narrowly because dsh has not published a stable compatibility
contract.

## Verification and Status

Automated verification covers registration contracts, cancellation plumbing,
Node runtime execution, type checking, bundling, and tarball contents. dsh
continues to be labelled experimental until a clean pinned-profile E2E proves:

1. `dsh plugin add` recognizes the bundle;
2. the profile loads the plugin;
3. all nine tools are discoverable;
4. `quant_quote` and a parameterized `quant_kline` complete against a real API.
