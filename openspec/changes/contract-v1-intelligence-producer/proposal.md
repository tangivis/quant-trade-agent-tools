# Proposal: Contract v1 Intelligence Producer

## Why

`quant_trade` 仍直接调用模型完成新闻标题情感、聚合情感、跳空叙事和翻译。为完成
Data & Domain Plane 与 Intelligence Plane 的运行时解耦，本仓库必须成为这些能力的
唯一 HTTP producer，同时保持现有 `/v1/analyze`、`/v1/chat` 和 MCP/CLI 行为不变。

## What Changes

- 在 REST Gateway 增加四个 contract v1 endpoint：
  - `POST /v1/enrich/headlines/sentiment`
  - `POST /v1/enrich/sentiment-summary`
  - `POST /v1/narratives/gap`
  - `POST /v1/translate`
- 增加可注入 fake structured-completion client 的 application service。
- 复用 `resolve_provider()` 和 OpenAI-compatible `chat/completions` transport。
- 使用 forced function/tool call 约束模型输出，并在 application service 再次校验。
- 标题情感最多执行一次 missing-ID repair；只返回请求 ID 的唯一子集。
- 所有成功响应统一返回 `contract_version`、`request_id`、`provenance` 和 `warnings`。
- `/v1/capabilities.intelligence_tasks` 只列出当前真正实现的任务。
- 通过 Gateway 既有 error envelope 映射 provider 配置、超时、429、HTTP 和结构错误。

## Non-Goals

- 不修改或 import `quant_trade`。
- 不访问产品数据库，不实现 job claim/result persistence。
- 不增加 order、cancel、position mutation 或自动实盘工具。
- 不迁移 legacy analyze，不实现 native/shadow orchestration。
- 本 change 不把 enrichment 暴露成新的 MCP tool；后续 MCP 必须复用本次 application
  service，而不是复制 provider 调用。

## Acceptance

- 四个 endpoint 的正常、边界、验证和 provider 错误测试通过。
- 标题 score 为有限数并 clamp 到 `[-1, 1]`；未知或重复 output ID 被拒绝。
- 初次缺 ID 时只对缺失项 repair 一次，repair 后仍缺失的 ID 显式返回。
- gap narrative 不超过 60 个 Unicode 字符且拒绝明显交易建议/展望。
- `/v1/capabilities` 不广告未实现 intelligence task。
- `/v1/analyze` 与 `/v1/chat` 回归测试不变。
- producer OpenAPI/contract test 覆盖四个新路径。
- `uv run pytest tests/ -v`、`bun run typecheck` 和适用构建尽量全绿。
