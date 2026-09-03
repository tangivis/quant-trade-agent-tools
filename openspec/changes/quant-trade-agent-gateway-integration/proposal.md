# Proposal: Quant Trade Agent Gateway Integration

## Why

`quant-trade-agent-tools` 已经把 CLI、MCP、pi/dsh adapter 和多模型 runtime 从
`quant_trade` 中独立出来，但产品调用方向仍然是外部 harness → agent-tools →
`quant_trade`。`quant_trade` 前端还不能通过稳定产品 API 调用新 agent，现有
4-agent LangGraph orchestration 也仍位于 `backend_llm`。

如果直接让 `quant_trade` import 新仓库、让浏览器成为 MCP client，或让 Rust
backend 代理到 agent 后再由 agent 回调同一 backend，都会重新产生代码耦合、
密钥暴露或难以运维的应用级循环依赖。

## Recommendation

在独立仓库增加一个**可选 REST Agent Gateway**，与现有 MCP 并列：

- MCP：面向 pi、Codex、Claude Code、dsh 等 agent harness。
- REST Gateway：面向 `quant_trade` 产品前端、移动端或其他业务系统。
- 两个入口复用同一个 `ToolRegistry`、provider resolver 和安全策略。
- 通过 nginx/反向代理把产品同源路径 `/agent-api/*` 路由到 Gateway，不在 Rust
  application code 中增加反向代理。
- 分阶段把 LangGraph orchestration 从 `quant_trade/backend_llm` 迁到独立 agent；
  首阶段保留 legacy `/agent/analyze` 作为兼容 provider，避免一次性改行为。

## Goals

- 让 `quant_trade` 产品可以稳定调用独立 agent，而不 import 它的源码。
- 让 Gateway 自己采集行情上下文，避免客户端传入伪造或过期价格/指标。
- 保持 MCP、CLI、REST 三个入口共享同一工具和安全边界。
- 支持 GPT、DeepSeek、Kimi、MiniMax、Ollama 与 custom provider。
- 支持 shadow comparison 和可回滚的分阶段迁移。
- 继续禁止券商下单、撤单和自动实盘执行。

## Non-Goals

- 本 change 不立即删除 `backend_llm`。
- 本 change 不把 Rust 行情、指标、回测或策略算法迁入 agent 仓库。
- 本 change 不实现持久对话记忆、用户账户系统或多租户计费。
- 本 change 不让浏览器直接持有模型 key、上游 API token 或 MCP transport。
- 本 change 不实现任何 order/cancel/live-trading tool。

## Proposed Public Surface

- `GET /health`
- `GET /v1/capabilities`
- `POST /v1/analyze`
- `POST /v1/chat`

Gateway 默认只监听 `127.0.0.1`，由反向代理提供 TLS、同源路径和外部认证。

## Impact

### `quant-trade-agent-tools`

- 新增可选 `gateway` dependency extra 和 `agent-tools gateway` 命令。
- 新增 REST request/response contract、context collector、auth、observability。
- 后续迁入或重新实现 orchestration，逐步替代 legacy analysis provider。

### `quant_trade`

- 第一阶段只修改反向代理和前端 API client，不改 Rust 业务算法。
- legacy `/agent/analyze` 在迁移期保留，作为 parity baseline 和 rollback。
- 完成 shadow verification 后再删除产品对 legacy agent endpoint 的直接依赖。

## Main Risks

- Gateway 与 legacy LangGraph 输出不一致。
- agent 回调行情 API 时形成流量放大。
- benchmark 等长任务被模型无意触发。
- provider、tool 或上游 API 错误被包装成正常分析。

通过 contract tests、shadow comparison、tool policy、最大迭代次数、结构化错误和
显式 capability/version contract 控制这些风险。
