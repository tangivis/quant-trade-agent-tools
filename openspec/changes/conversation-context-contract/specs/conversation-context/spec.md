# Conversation Context and Public Release Delta

## ADDED Requirements

### Requirement: untrusted context remains data

The chat producer SHALL accept a bounded optional conversation summary, SHALL place it after the fixed
system policy as user-role structured data, and SHALL preserve ordered recent history. Caller-controlled
summary text SHALL NOT become a system message.

#### Scenario: hostile stored summary

- Given a stored summary containing instruction-like text
- When the Gateway constructs the provider request
- Then the fixed policy is the only system message
- And the stored summary is serialized as untrusted data

### Requirement: canonical native analysis

The canonical analyze client, CLI, MCP and harness schemas SHALL accept only a supported symbol and an
optional bounded question. They SHALL call `POST /v1/analyze` on the configured Gateway using its separate
Bearer credential. They SHALL NOT call the legacy `/agent/analyze` product endpoint or accept caller facts.

#### Scenario: analyze dispatch

- Given a supported symbol and question
- When a harness invokes `quant_analyze`
- Then the client sends the exact v1 request to the Gateway
- And the product market API receives no request from that dispatch

### Requirement: public package integrity

Pi and DSH SHALL expose the same canonical tool schemas and cancellation behavior. All published version
identities SHALL be `0.4.0`, package descriptions SHALL report the current 12-tool boundary, and published
metadata SHALL reference the public source repository without private coordinates.

#### Scenario: package release gate

- Given a release candidate checkout
- When CI runs tests, lint, typecheck, builds and pack inspection
- Then each gate succeeds
- And the archives contain no workspace-only runtime dependency, local path or credential

### Requirement: public source is independently verifiable

The public source repository SHALL run a credential-free pull-request workflow without requiring access
to private CI or registry/provider credentials.

#### Scenario: public pull request

- Given a pull request targeting public `main`
- When the public workflow runs
- Then it executes Python tests and lint, TypeScript tests and typecheck, all builds, and Python/npm package
  inspection
- And it grants only read access to repository contents
- And every external action is pinned to an immutable commit SHA
- And it does not enable real-provider smoke or registry publication
