# Native Analysis Provider — Implementation Plan

## Scope

只修改 `quant-trade-agent-tools`，让 Gateway 默认 native analyze，不再依赖 legacy Python
`/agent/analyze`。legacy 保留为显式 rollback；shadow、wish、Twitter 和 durable worker 不在
本切片范围内。

## TDD Sequence

1. 在 `tests/test_gateway_services.py` 写 native provider 红测试：
   - 完整 ContextSnapshot -> consumer-compatible layered response；
   - facts/as_of/source warnings 完全来自 snapshot；
   - 空 facts、缺少 derived required facts 时不调用模型；
   - action/trend/confidence/approved/summary/risk_notes 边界；
   - config/timeout/429/HTTP/invalid structured output mapping。
2. 在 `tests/test_gateway_app.py`/`test_gateway_settings.py` 写红测试：
   - `GatewaySettings()` 和 env 默认 native；
   - native/legacy 可用，shadow 拒绝；
   - app 默认 provider selection 与显式 legacy rollback；
   - capabilities 不广告 shadow。
3. 在 `tests/test_gateway_openapi.py` 写 analyze request/response producer snapshot 红测试。
4. 运行 focused tests，记录实现缺失/默认值错误/OpenAPI 缺失的红灯。
5. 从 enrichment provider boundary 提取 `StructuredModelExecutor`，保持既有测试全绿。
6. 在 `gateway/services.py` 实现 `NativeAnalysisProvider` 与严格 schema/normalization。
7. 在 `gateway/config.py` 默认 native、允许 explicit legacy、拒绝 shadow。
8. 在 `gateway/app.py` 按 mode 选择 provider，修正 capabilities，为 analyze 增加 response model。
9. 更新 producer OpenAPI snapshot，并验证与 runtime schema exact compatibility。
10. 运行 focused tests转绿后重构重复 validation/prompt/constants。
11. 更新 CHANGELOG、README、架构/详细功能、验证报告、OpenSpec tasks 和 handoff。
12. 运行 Python、TS、typecheck、build、packaging、diff/no-secret/no-broker 边界审计。

## Rollback

运行时紧急回滚只需配置：

```text
TRADE_AGENT_ORCHESTRATION_MODE=legacy
```

它恢复既有 `LegacyAnalysisProvider`。不需要恢复旧 Python auto pipeline，也不改变
`quant_trade` 的产品持久化职责。
