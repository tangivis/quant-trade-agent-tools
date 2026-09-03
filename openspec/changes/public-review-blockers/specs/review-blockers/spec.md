# Public Review Blocker Delta

## ADDED Requirements

### Requirement: explicit legacy analysis rollback remains callable

Legacy analysis mode SHALL send its derived snapshot payload to the product legacy endpoint through a
dedicated client method. It SHALL NOT invoke the canonical native Gateway analyze method or recurse into
`POST /v1/analyze`.

#### Scenario: operator selects legacy mode

- Given a complete server-owned context snapshot
- When `LegacyAnalysisProvider` analyzes it
- Then the exact legacy payload is sent to product `POST /agent/analyze`
- And canonical native analyze is not called

### Requirement: Gateway chat binds selected symbol

Gateway chat SHALL expose the validated request symbol as untrusted model context and SHALL use it as the
default for symbol-scoped tool calls that omit `symbol`.

#### Scenario: model omits symbol for selected Murata chat

- Given chat selected `6981.T`
- When the model calls quote without a symbol
- Then the runtime calls quote with `6981.T`
- And no request defaults to `9984.T`

#### Scenario: model calls a global feed

- Given any selected chat symbol
- When the model calls news or sentiment
- Then the runtime does not inject a symbol field
