# Proposal: Opt-in Real Provider Staging Smoke

## Problem

Contract、mock transport 与 fake service tests 已覆盖 provider-neutral structured executor，
但尚未验证真实 OpenAI-compatible provider 对 translation 和 wish structured tool calls 的支持。
直接把真实调用放进默认 tests 会造成意外网络访问、配额消耗和 secret 泄露风险。

## Scope

- 新增默认绝不联网的 staging smoke runner。
- 只有 `RUN_REAL_PROVIDER_E2E=1` 且选定 provider key 非空时才构造 service 并调用网络。
- 真实验证 translation、wish clarifying 和 wish confirming 三个 structured calls。
- 复用 `resolve_provider()`、`GatewayIntelligenceService` 和共享
  `StructuredModelExecutor`，不增加 provider-specific transport。
- 输出固定脱敏摘要：provider、model、contract、每项 latency、phase 和结构校验结果。
- 新增 mock/gate/redaction tests 与一个默认 skip 的真实 provider pytest case。
- 修复 producer snapshot/runtime parity：冻结已有 `/v1/chat` 与 `/v1/capabilities`，不降低
  cross-repo verifier 的 required routes。
- 真实 smoke 完成后新增 `docs/mr/` 独立 MR draft，供后续人工建 MR 使用；本切片不 commit/
  push 或调用 GitLab。

## Non-goals

- 不输出 provider base URL、key、prompt、history、翻译正文、wish reply 或原始 provider body。
- 不保存模型响应。
- 不持有 GitLab token、不创建 issue、不调用产品 mutation API。
- 不让默认 CI 或普通 `uv run pytest` 访问外网。

## Acceptance

- 未设置 opt-in：service factory 不执行，报告为 sanitized skipped。
- opt-in 但 key 缺失：service factory 不执行，报告为 sanitized skipped。
- opt-in + key：三次真实 structured call 全部通过 phase/shape/provenance 校验。
- GatewayError/未知异常报告不包含异常 message 或 secret。
- 默认 full suite 显示 live case skipped；显式 staging 命令可独立执行一次。
- mock/full/build/package/security 门禁先通过，再执行真实 MiniMax smoke。
- snapshot verifier 覆盖 GET/POST method，并对 chat/capabilities 的 runtime request/response
  contract 做 exact compatibility 检查。
- MR draft 记录 target/source/title、producer-first dependency、contract/security、真实 provider
  脱敏证据、完整测试、rollout/rollback、dsh experimental 和未实现 shadow/durable worker。
