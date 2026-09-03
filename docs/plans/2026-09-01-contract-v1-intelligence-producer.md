# Contract v1 Intelligence Producer — Implementation Plan

## Scope

只修改 `quant-trade-agent-tools`，实现 frozen contract v1 的四个模型驱动 producer
endpoint。`quant_trade`、产品 DB、broker mutation、legacy analyze/chat 行为均不在范围内。

## TDD Sequence

1. 在 `tests/test_gateway_intelligence.py` 写 application service 红测试：
   - headline 正常、clamp、顺序、未知/重复 ID；
   - 一次 missing-ID repair 和 repair 后仍 missing；
   - summary metadata/枚举/score；
   - gap 长度/建议文本；
   - translation；
   - provider config、timeout、429、HTTP、invalid structured output。
2. 在 `tests/test_gateway_app.py` 写四个 REST endpoint、validation、request ID、capabilities
   和 injected fake service 红测试。
3. 在 `tests/test_gateway_openapi.py` 写 producer path/schema snapshot 红测试。
4. 运行 focused tests 并保存失败摘要，确认失败原因是实现缺失而非测试环境。
5. 在 `gateway/models.py` 实现严格 v1 input/output models。
6. 新建 `gateway/intelligence.py`：
   - `StructuredOutputClient` protocol；
   - OpenAI-compatible forced tool-call implementation；
   - `GatewayIntelligenceService` normalization/repair/error mapping。
7. 在 `gateway/app.py` 注入 service、注册四个 endpoint、更新 capabilities。
8. 产出 producer OpenAPI contract artifact，并以 runtime compatibility test 固定路径和
   request/response schema。
9. 运行 focused tests 转绿；重构重复的 provider error mapping和 common response metadata。
10. 更新 README、CHANGELOG、Gateway 架构、详细功能、验证证据和 handoff。
11. 运行全套 Python、TS、typecheck、build、diff/no-secret/no-order audit。

## Rollback

新 endpoint 和 service 是加法变更。回滚时删除新 routes/models/service/OpenAPI artifact，
现有 `/v1/analyze`、`/v1/chat`、MCP、CLI 不需改变。
