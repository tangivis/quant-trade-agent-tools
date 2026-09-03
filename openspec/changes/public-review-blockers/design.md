# Design

## Legacy rollback separation

`QuantTradeClient.analyze(symbol, question)` remains the canonical Gateway method. A new
`legacy_analyze(payload)` method owns the legacy product `/agent/analyze` request and product credential.
`LegacyAnalysisProvider` is the only Gateway component that invokes it. Separate names prevent recursive
Gateway dispatch and make removal of the rollback path explicit later.

## Chat symbol binding

`GatewayChatService` passes its already validated symbol to `OpenAICompatibleAgent.run` as
`selected_symbol`. The runtime serializes it as bounded JSON in a user-role context record, never as a
system instruction. Before tool dispatch, it injects the selected symbol only when all conditions hold:

1. a Gateway caller supplied `selected_symbol`;
2. the selected tool is in the canonical symbol-scoped allowlist; and
3. the model omitted the `symbol` property.

An explicit tool symbol remains unchanged and is validated normally by `ToolRegistry`. Global news and
sentiment never receive synthetic symbol fields.

## Compatibility

The additional `selected_symbol` runtime parameter is optional, so standalone CLI agent calls retain their
existing behavior. Provider messages, tool schemas and public REST request/response contracts do not
change.
