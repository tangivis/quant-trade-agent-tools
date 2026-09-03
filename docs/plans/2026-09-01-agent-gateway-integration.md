# Agent Gateway 集成实施计划

## 原则

- 本计划必须在架构文档获批后才进入编码。
- 所有行为按 OpenSpec 场景先写失败测试，再实现最小代码。
- `trade_agent` 和 `quant_trade` 分别建立 change，不跨仓库混合提交。
- 第一阶段只做 Gateway facade，不改变 legacy 分析行为。

## Phase 1：Gateway 基础

1. 在 `pyproject.toml` 增加可选 `gateway` extra。
2. 先写 CLI 注册/缺少 extra/启动参数失败测试。
3. 实现 `agent-tools gateway` 延迟 import。
4. 先写 `/health`、`/v1/capabilities` contract tests。
5. 实现最小 FastAPI app 和 Pydantic schemas。

验收：未安装 gateway extra 时 CLI/MCP 仍正常；安装后 in-process tests 全绿。

## Phase 2：认证与错误

1. 先写无 token、错误 token、正确 token 测试。
2. 实现 `TRADE_AGENT_API_TOKEN` Bearer middleware/dependency。
3. 先写统一 error envelope 测试。
4. 覆盖 upstream timeout、HTTP error、invalid JSON、provider 429、iteration limit。
5. 验证错误不能转成成功 HOLD。

验收：所有失败都有 request id、code、retryable，且不泄露内部凭据。

## Phase 3：ContextCollector

1. 定义 `ContextSnapshot` 和 source status。
2. 先写完整成功、单源失败、多源失败、超时和时间戳测试。
3. 通过 canonical `ToolRegistry` 并行调用 quote/kline/trending/signals/sentiment/news。
4. 验证调用方 live-looking values 不成为权威 facts。
5. 为 partial context 生成明确 warnings。

验收：不编造缺失值；相同 fixture 生成确定性 snapshot。

## Phase 4：Legacy Analyze Facade

1. 从当前 `backend_llm /agent/analyze` 保存脱敏 fixtures。
2. 定义 `AnalysisProvider` protocol。
3. 先写 legacy request mapping 和 response normalization 测试。
4. 实现 `/v1/analyze` legacy mode。
5. 输出 facts/analysis/decision/provenance/warnings 分层结构。

验收：结构化字段与 legacy baseline 一致，且 UI 所需信息没有丢失。

## Phase 5：Chat Gateway

1. 先写 stateless history、max iterations 和 provider error tests。
2. 复用 `OpenAICompatibleAgent`，避免第二套 tool loop。
3. 先写 expensive-tool policy 测试。
4. 默认禁止 benchmark；显式 allow 后才开放。
5. 验证任何模式都没有 order/cancel tool。

验收：chat/MCP 使用同一 registry；工具 schema 无漂移。

## Phase 6：部署与产品接入

1. 在 `quant_trade` 建立单独 OpenSpec 与 plan。
2. 添加 systemd unit 和环境变量示例。
3. 添加 nginx `/agent-api/` 同源路由。
4. 前端新增 Gateway client 与 feature flag。
5. 验证 Gateway 停止时行情页面仍可用。
6. 验证配置级和前端 flag 两种回滚。

验收：不向浏览器发送 provider/upstream key；旧分析路径仍可恢复。

## Phase 7：Native Shadow

1. 先定义 parity dataset 和阈值。
2. TDD 实现 `NativeAnalysisProvider`。
3. 实现 shadow runner 和结构化 diff。
4. 记录 action、confidence、approved、risk notes、latency、cost。
5. 完成 soak report 后提交切换评审。

验收：没有显式批准不得切 native 默认值。

## Phase 8：退役 Legacy

1. native 上线后保留 legacy fallback 一个 release。
2. 确认没有调用者使用旧 endpoint。
3. 在 `quant_trade` 独立 change 删除 superseded orchestration。
4. 更新部署、runbook、架构图和 changelog。

## 验证命令

预期继续使用：

```bash
uv run pytest tests/ -v
bun test packages/
bun run typecheck
bun run build
uv build
```

Gateway 实现后另加 in-process contract tests 和部署 smoke，不使用生产模型 key 作为 CI
前置条件。
