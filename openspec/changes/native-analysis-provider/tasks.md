# Tasks

## 1. SDD

- [x] 读取两个仓库 handoff 和 `quant_trade` analyze consumer fixture。
- [x] 定义 native structured contract、context gate、mode selection 和 rollback。
- [x] 写超过三个文件的实施计划。

## 2. Native Provider TDD

- [x] 先写正常 layered response 与 server-owned facts 红测试。
- [x] 先写空/缺失 context 不调用模型红测试。
- [x] 先写 invalid shape/action/confidence/summary/risk notes 红测试。
- [x] 先写 timeout、429、HTTP/config error 红测试。
- [x] 实现共享 structured executor 和 `NativeAnalysisProvider`。

## 3. Settings / Gateway TDD

- [x] 先写默认 native、显式 legacy、shadow 拒绝红测试。
- [x] 先写 capabilities active/available/planned 红测试。
- [x] 让 app 根据 mode 选择 native/legacy，并保持 provider injection。
- [x] 为 analyze 增加严格 response model，保持 consumer fixture compatibility。

## 4. Producer OpenAPI

- [x] 先写 analyze request/response snapshot compatibility 红测试。
- [x] 更新 `openapi/agent-gateway-v1.json` 并验证 wheel/sdist 包含。

## 5. Regression

- [x] enrichment 四 endpoint 与 chat focused tests 全绿。
- [x] legacy provider 显式 rollback 测试全绿。
- [x] MCP/CLI/工具边界无变化。

## 6. Documentation / Handoff

- [x] 更新 CHANGELOG、README、架构、详细功能和验证证据。
- [x] 更新 `docs/handoffs/CURRENT.md`。
- [x] 记录 red/green/refactor 证据。

## 7. Verification

- [x] focused/full Python 全绿。
- [x] TypeScript tests/typecheck/build 全绿。
- [x] `uv build`、OpenAPI packaging 和 `git diff --check` 全绿。
- [x] no DB/import/order/cancel/broker mutation 审计通过。
