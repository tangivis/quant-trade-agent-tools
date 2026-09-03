# Proposal: Wish Interpretation Producer

## Problem

`quant_trade` 已完成 `/api/wish` consumer、GitLab issue client 和产品侧 mutation 边界，
但 `POST /v1/interpret/wish` producer 尚不存在。产品因此无法把多轮愿望对话交给独立
Intelligence Plane，也不能在确认后安全地创建 issue。

## Scope

- 新增 `POST /v1/interpret/wish`。
- 输入只接受当前 `message` 和有界 `history`，保持无状态。
- 使用共享 provider-neutral `StructuredModelExecutor` 和 forced structured tool/schema。
- 严格验证 `clarifying|confirming|confirmed` 状态与阶段相关字段。
- confirming/confirmed 必须重复完整、从对话重建的 validated wish payload。
- 更新 capabilities、producer OpenAPI、发布物、测试和文档。

## Non-goals

- 不保存 wish session 或 conversation history。
- 不持有 GitLab token、不创建 issue。
- 不调用 `quant_trade` mutation API 或数据库。
- 不增加 order、cancel、broker 或自动交易能力。
- 不迁移 durable enrichment worker 或退役 legacy analyze。

## Acceptance

- clarifying 可只返回 phase；confirming/confirmed 必须包含完整结构。
- phase/type/priority、空值、超长值、空 requirements 和额外字段均严格拒绝。
- provider config、timeout、429、HTTP 和 invalid structured output 使用统一 Gateway error envelope。
- reply 与结构化自然语言字段为简体中文；模型输出不满足基本中文约束时失败。
- capabilities 只在 endpoint 实现后广告 `wish_interpretation`。
- `quant_trade` consumer fixture、runtime OpenAPI snapshot 和所有现有回归测试通过。
