# Proposal: Native Analysis Provider

## Why

`quant_trade` 已改为每五分钟调用 `POST /v1/analyze`，验证 layered response 后自行写入
`agent_analysis`，旧 Python auto pipeline 不再自启动。但 Gateway 的 analyze 仍通过
`LegacyAnalysisProvider` 回调 `backend_llm /agent/analyze`，因此模型执行与编排尚未真正
离开 Data Plane。

本 change 在 Intelligence Plane 实现 native analyze，使默认调用链只依赖
`ContextCollector`、provider-neutral structured model infrastructure 和 `quant_trade`
公开事实 API。

## What Changes

- 新增 `NativeAnalysisProvider`，以 server-owned `ContextSnapshot` 为唯一事实输入。
- 通过 OpenAI-compatible forced function/tool call 生成严格结构化分析和 decision support。
- 输出保持现有 layered contract：`facts`、`analysis`、`decision`、`provenance`、`warnings`。
- `GatewaySettings` 默认 orchestration mode 改为 `native`，允许 `native|legacy`。
- `legacy` 只作为显式配置回滚路径；未实现的 `shadow` 继续在启动时拒绝。
- `/v1/capabilities` 准确报告 active/available/planned。
- 为 `/v1/analyze` 增加严格 response model，并把其 request/response 纳入 producer OpenAPI。
- 保持 enrichment、chat、MCP/CLI 和 broker/tool 边界不变。

## Non-Goals

- 不修改 sibling `quant_trade`，不访问其数据库或内部模块。
- 不实现 shadow comparison。
- 不迁移 wish agent 或 Twitter query planning/scoring。
- 不删除 legacy client/config；它仍保留一个显式 rollback release。
- 不增加 order、cancel、position mutation 或任何 broker execution tool。

## Acceptance

- 默认 Gateway `/v1/analyze` 使用 `NativeAnalysisProvider`，不调用 legacy `/agent/analyze`。
- 明确配置 `TRADE_AGENT_ORCHESTRATION_MODE=legacy` 时仍可使用旧 provider。
- `native` 只接受完整 server-owned context；空或缺少必需派生事实时返回可重试
  `CONTEXT_INCOMPLETE`。
- structured output 的 action 仅为 `BUY|HOLD|SELL`，confidence 为有限 `[0,1]`，summary
  非空，risk notes 有界；任何违规使用 `MODEL_RESPONSE_ERROR`。
- timeout、429、HTTP/provider config 错误复用现有 Gateway error envelope。
- analyze response 与 `quant_trade` consumer fixture 兼容，并始终包含
  `decision_support_only` warning。
- capabilities 在默认配置下报告 active native、available native/legacy、planned 空列表。
- enrichment/chat/analyze/legacy/full suites、OpenAPI compatibility、build 和边界审计全绿。
