# Tasks

## 1. SDD

- [x] 读取仓库 AGENTS、Herdr runbook、frozen contract v1 和现有 Gateway。
- [x] 定义 endpoint、application service、structured output、repair 和错误语义。
- [x] 写超过三个文件的实施计划。

## 2. Contract Models TDD

- [x] 先写 request extra/duplicate ID/边界与 OpenAPI path 红测试。
- [x] 实现四类 request/response Pydantic models。
- [x] 验证现有 analyze/chat models 与行为无回归。

## 3. Application Service TDD

- [x] 先写 headline 正常、clamp、requested subset、duplicate、repair 与 residual missing 红测试。
- [x] 先写 summary/gap/translation 正常和边界红测试。
- [x] 先写 config/timeout/429/HTTP/structured-response 红测试。
- [x] 实现 injectable `StructuredOutputClient` 与 `GatewayIntelligenceService`。
- [x] 实现 OpenAI-compatible forced tool-call client。

## 4. REST Producer TDD

- [x] 先写四个 route 的 request mapping、metadata、error-envelope 红测试。
- [x] 注入 application service 并实现四个 route。
- [x] 更新 capabilities，仅广告已实现 task。
- [x] 验证 `X-Request-ID` 与成功 body request ID 一致。

## 5. Producer Contract

- [x] 添加 producer OpenAPI snapshot 或等价稳定 contract artifact。
- [x] 添加 snapshot/runtime compatibility test。

## 6. Documentation

- [x] 更新 README endpoint 与运行边界。
- [x] 更新 Gateway 架构和详细功能文档。
- [x] 更新 CHANGELOG 和 `docs/handoffs/CURRENT.md`。
- [x] 记录 red/green/refactor 验证证据。

## 7. Verification

- [x] focused Gateway tests 全绿。
- [x] `uv run pytest tests/ -v` 全绿。
- [x] `bun test packages/`、`bun run typecheck`、构建尽量全绿。
- [x] `git diff --check` 与 no-secret/no-order-tool audit 通过。
