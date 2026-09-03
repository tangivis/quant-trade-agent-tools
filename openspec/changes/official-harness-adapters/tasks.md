# Tasks

## 1. SDD

- [x] Record the host lifecycle, runtime, packaging, and compatibility gaps.
- [x] Define the stable CLI/MCP boundary and experimental dsh gate.
- [x] Write the multi-file implementation plan.

## 2. TDD: Red

- [x] Add a failing bridge test proving published runtime code has no Bun API.
- [x] Add a failing bridge test for caller cancellation.
- [x] Replace dsh shim assertions with failing official plugin/tool assertions.
- [x] Add failing package-manifest assertions for `dsh.bundle` and pinned peers.

## 3. TDD: Green and Refactor

- [x] Implement the minimal Node-compatible subprocess bridge.
- [x] Implement the official dsh `apply`/`inject` tool plugin.
- [x] Add the dsh composition patch and externalize host-owned packages.
- [x] Narrow pi and dsh peer dependency compatibility ranges.
- [x] Remove obsolete consumer-shim code and manifest entries.

## 4. Documentation and Verification

- [x] Update package READMEs, repository integration/publish docs, and changelog.
- [x] Run all TypeScript tests and type checking.
- [x] Build both adapters and run a plain-Node bundle smoke test.
- [x] Run Python tests and both Python/TypeScript builds.
- [x] Inspect npm tarballs for manifests, workspace dependencies, and paths.
- [x] Record red/green/refactor evidence and remaining dsh E2E limitation.
