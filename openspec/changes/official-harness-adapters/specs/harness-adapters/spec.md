# Harness Adapter Requirements

## ADDED Requirements

### Requirement: Runtime-Neutral CLI Bridge

Published TypeScript adapters MUST run in the Node.js runtime supported by the
host and MUST NOT require a global Bun API.

#### Scenario: Plain Node execution

- WHEN a built adapter invokes the Python CLI from a Node.js process
- THEN the bridge spawns the configured command, captures stdout and stderr,
  and returns its exit status without referencing `Bun`.

#### Scenario: Harness cancellation

- WHEN the harness aborts a tool execution
- THEN the bridge terminates the owned subprocess, waits for settlement, and
  returns a non-success result that the adapter exposes as a tool error.

### Requirement: pi Native Extension

The pi package MUST use the documented package manifest and extension tool API.

#### Scenario: Tool registration

- WHEN pi invokes the package's default extension factory
- THEN exactly nine `quant_*` tools are registered through `registerTool`.

#### Scenario: Compatibility metadata

- WHEN the pi npm manifest is inspected
- THEN the host peer dependency declares the tested compatibility range rather
  than an unconstrained wildcard.

### Requirement: DeepSeek Harness Tool Plugin

The dsh adapter MUST use the documented Cordis plugin lifecycle and tool
registry while it remains experimental.

#### Scenario: Plugin lifecycle

- WHEN dsh loads the module
- THEN it exports a plugin name, declares the `tools` injection, and exposes an
  `apply(ctx)` entry point.

#### Scenario: Model-facing registration

- WHEN `apply(ctx)` runs with the tools service available
- THEN exactly nine `quant_*` definitions are registered through
  `ctx.tools.register()` with parameters, output, renderer, and executor.

#### Scenario: Cancellation propagation

- WHEN dsh calls a registered tool with an execution signal
- THEN the same signal is forwarded to the shared subprocess bridge.

#### Scenario: Installable bundle

- WHEN `dsh plugin add` inspects the npm package
- THEN `dsh.bundle.patch` identifies a packaged composition patch that inserts
  the adapter by package name.

### Requirement: Repository Independence

Native adapters MUST depend on `quant_trade` only through the standalone
Python CLI's published HTTP boundary.

#### Scenario: Clean installation

- WHEN an adapter tarball is installed outside this workspace
- THEN it contains no `workspace:*` runtime dependency, sibling
  `../quant_trade` reference, database dependency, or local absolute path.

### Requirement: Experimental dsh Status

dsh documentation MUST NOT claim stable support before pinned-release E2E.

#### Scenario: Automated verification only

- WHEN unit tests, type checking, bundle builds, and package inspection pass
  without a real dsh profile
- THEN dsh remains labelled experimental and the missing E2E is documented.
