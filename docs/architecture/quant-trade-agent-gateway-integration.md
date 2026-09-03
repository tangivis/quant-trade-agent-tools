# quant_trade 调用独立 Agent 的推荐架构

本页是产品集成的详细设计。公开的规范性职责和安全边界分别以仓库根目录
`ARCHITECTURE.md` 与 `SECURITY.md` 为准；部署地址、内部拓扑、账户和真实 provider/model
选择不属于本页。

## 结论

推荐由独立的 Product/Data/Domain Plane 与完整 Intelligence Plane 采用：

> **独立 REST Agent Gateway + 现有 MCP 双接口，nginx 同源路由，LangGraph 分阶段迁移。**

不要让 `quant_trade` import agent 包；不要让浏览器直接成为 MCP client；不要在
Rust backend 内增加“调用 agent、agent 再回调 Rust”的产品代理链路。

本架构的 Gateway、contract v1 同步 enrichment producer 和默认 native analyze 已在本仓库
实现。`quant_trade` Rust 已按周期调用 `/v1/analyze`、验证 layered response 并自行持久化；
wish consumer/producer 与产品侧 GitLab mutation 边界也已完成。durable jobs 和 legacy 最终
退役仍需分阶段完成。代码评审和评审回复的 provider、prompt 与结构化输出也已迁入本仓，
`quant_trade` 只持有 HTTP consumer，不再需要本地 coding-agent 编排。

## 1. 逻辑层级

```text
pi / dsh / MCP harness / CLI
              |
              v
       quant-trade-agent-tools
       - ToolRegistry
       - MCP
       - multi-model chat
       - native layered analysis
       - stateless wish interpretation
       - stateless code review/respond
       - HTTP normalization
              |
       +------+----------------+
       |                       |
Product/Data/Domain      model provider APIs
事实/域逻辑/持久化         structured output
       |
       +---- legacy analysis service (explicit rollback only)
```

已经解耦的是 harness、MCP、CLI、模型 preset、工具协议和产品定时 analyze 路径：

- Gateway 默认 native，直接使用 provider-neutral model infrastructure，不调用 legacy
  `/agent/analyze`；
- `quant_trade` Rust 每五分钟请求 layered analysis，并由产品自己的写路径保存；
- legacy provider 仍保留为配置级显式回滚；
- wish interpretation 已迁移，GitLab token/issue 创建仍只在产品侧；
- code review/respond 已迁移，所有模型调用/prompt 位于本仓且 producer 无副作用；
- Twitter 已成为产品侧 raw connector，其情感 enrichment 走共享 Gateway 调度路径；
- 四类同步 enrichment 尚无 durable job worker。

因此 analyze 的运行时依赖已经解开，但旧 orchestration 的剩余职责尚未全部退役。

## 2. 推荐部署关系

```text
                         ┌─────────────────────────┐
Browser / Mobile ─HTTPS─▶│ nginx / reverse proxy   │
                         └───────┬─────────┬───────┘
                                 │         │
                           /api/*│         │/agent-api/*
                                 ▼         ▼
                  Product/Data/Domain   Intelligence Gateway
                           ▲                  │
                           │ market tools     │ model APIs
                           └──────────────────┤
                                              │ transition only
                                              ▼
                                      backend_llm :8003

pi / Codex / Claude / dsh ──MCP──▶ same trade_agent ToolRegistry
```

关键点：

1. 产品使用 REST，agent harness 使用 MCP。
2. REST 与 MCP 复用同一个 ToolRegistry、client normalization 和安全策略。
3. 浏览器只访问同源 `/agent-api/*`，不持有模型 key 或上游 token。
4. nginx 做路由，Rust application 不做代理，避免应用级依赖循环。
5. legacy LangGraph 只在迁移期作为兼容 provider 和回滚路径。

## 3. 为什么不只用 MCP

MCP 非常适合模型/harness：工具发现、typed schema、tool call 都是标准能力。但产品
前端需要的是稳定业务 API，而不是自己管理 MCP session 和工具循环。

| 使用者 | 推荐接口 | 原因 |
|---|---|---|
| pi/Codex/Claude/dsh | MCP | harness 已有模型和 tool lifecycle |
| shell/自动化脚本 | CLI | 简单、可观测、无常驻服务 |
| quant_trade Web UI | REST Gateway | 同源、可鉴权、稳定 response contract |
| 其他服务 | REST 或 MCP | 根据是否需要自主 tool loop 选择 |

双接口不是重复业务逻辑；它们只是两个 transport adapter。

## 4. 服务边界

### `quant_trade` 保留

- Yahoo/PG 行情和 K 线；
- 技术指标、趋势 regime、交易信号；
- 新闻、Twitter 情报与情感数据；
- backtest、benchmark 和策略算法；
- TSE 日历、财报、风控等业务真相。

### `trade_agent` 负责

- 工具 schema 和上游 contract normalization；
- MCP、CLI、pi/dsh adapter；
- 多模型 provider 配置；
- 产品 REST Gateway；
- ContextSnapshot 收集和验证；
- agent orchestration、tool policy、最大迭代次数；
- facts/analysis/decision/provenance 分层输出；
- native 默认与 legacy 显式回滚策略；
- 标题情感、聚合情感、gap narrative、translation 的 provider-neutral application service。
- 无状态 wish interpretation；GitLab issue mutation 明确保留在 `quant_trade`。
- 无状态 code review/respond；diff、project context 和讨论 context 都按不可信数据处理。

### 反向代理负责

- TLS；
- 同源路由；
- 外部认证和限流；
- 请求体大小限制；
- 不向浏览器暴露内部端口。

## 5. Gateway API 建议

| Method | Path | 用途 | 是否调用模型 |
|---|---|---|---|
| GET | `/health` | process liveness | 否 |
| GET | `/v1/capabilities` | contract、工具、provider、模式发现 | 否 |
| POST | `/v1/analyze` | 自动收集上下文并给出结构化决策支持 | 是/native |
| POST | `/v1/chat` | 有界工具调用对话 | 是 |
| POST | `/v1/enrich/headlines/sentiment` | 批量标题情感与一次 missing-ID repair | 是 |
| POST | `/v1/enrich/sentiment-summary` | 多来源聚合情感 | 是 |
| POST | `/v1/narratives/gap` | 事实型跳空叙事 | 是 |
| POST | `/v1/translate` | 翻译到简体中文 | 是 |
| POST | `/v1/interpret/wish` | 多轮愿望澄清/确认，confirmed 重建完整 payload | 是 |
| POST | `/v1/review/code` | diff/context 代码评审，返回 review 和严格 verdict | 是 |
| POST | `/v1/review/respond` | message/context 评审回复 | 是 |

`/v1/capabilities.intelligence_tasks` 是运行时 feature discovery：只有实现并通过 contract
tests 的任务才能出现。enrichment、analyze、wish 与 review 的 producer snapshot 位于
`openapi/agent-gateway-v1.json`，consumer 应固定 snapshot 而不是复制手写 schema。

### Code review 边界

`/v1/review/code` 只接受 1..120000 字符的非空 diff 和可选、最多 20000 字符的非空
`project_context`，输出 1..12000 字符 review 与 `LGTM|NEEDS_CHANGES` verdict。
`/v1/review/respond` 只接受 1..8000 字符 message 和可选、最多 20000 字符 context，输出
1..8000 字符 reply。两者都返回 v1 request ID、provider/model provenance 和 warnings。

模型只获得 forced structured schema；输入中伪装成 prompt 的内容仍是待评审数据。producer
不 checkout/修改代码，不执行命令，不访问 GitLab 或产品数据库，也不持久化请求/响应。

### `/v1/analyze` 不应接收什么

不应让客户端把 `price`、`rsi`、`adx`、`news_sentiment` 当成权威事实传入。否则
前端缓存、用户输入或其他调用者可能把过期/伪造数值送入风控决策。

客户端只提供：

- `symbol`；
- 可选问题；
- 分析模式；
- 非权威约束或备注。

Gateway 自己通过 canonical `ToolRegistry` 并行调用
`quote/kline/trending/signals/sentiment/news`，生成带 `as_of` 和
source status 的 `ContextSnapshot`。

### 输出必须分层

```text
facts       上游直接数据，不含模型猜测
analysis    模型/规则解释
decision    action/confidence/approved/risk_notes
provenance  provider/model/tools/request_id
warnings    延迟行情、缺失数据、fallback 等
```

这样前端可以分别展示“事实”和“AI 意见”，也便于 shadow comparison。

## 6. 迁移 LangGraph 的方法

不建议一次性复制 `backend_llm/src/agents/graph.py` 后立即切流量。推荐 provider
抽象：

```text
AnalysisProvider
  ├── LegacyAnalysisProvider
  │     └── HTTP POST backend_llm /agent/analyze
  └── NativeAnalysisProvider
        └── trade_agent 自有 orchestration + providers + tools
```

运行模式：

| Mode | 用户看到 | 用途 |
|---|---|---|
| `native` | native layered result | 默认生产路径 |
| `legacy` | legacy 结果 | 显式配置的紧急回滚 |
| `shadow` | 无 | 未实现；启动时拒绝且 capabilities 不广告 |

如果未来另立 OpenSpec 实现 shadow，至少比较：

- BUY/HOLD/SELL 或最终 action；
- confidence 差异；
- approved 差异；
- risk_notes 是否遗漏高风险项；
- context/tool 是否完整；
- 总延迟、模型错误率、上游错误率。

建议满足明确阈值并稳定运行一段时间后再切换，不能只凭几次人工对话判断 parity。

## 7. 长任务与工具政策

`benchmark` 可能运行 5–10 分钟，不应允许普通 chat 自动触发。

推荐 policy：

- `/v1/analyze` 永远不调用 benchmark；
- `/v1/chat` 默认 `allow_expensive_tools=false`；
- 只有用户明确请求并设置 allow flag 时才开放 benchmark；
- order/cancel 工具无论任何 flag 都不存在；
- tool loop 继续受 `max_iterations` 限制。

未来如果产品需要 benchmark，最好单独设计 job API：submit/status/result，而不是把
同步长任务塞进普通 chat request。

## 8. 安全建议

### 密钥分层

| 凭据 | 保存位置 | 浏览器可见 |
|---|---|---|
| Provider API key | Gateway env/systemd credential | 否 |
| `QUANT_TRADE_API_TOKEN` | Gateway env/systemd credential | 否 |
| `TRADE_AGENT_API_TOKEN` | reverse proxy/server | 否 |
| 用户登录 cookie/token | 产品既有安全层 | 按现有策略 |

### 日志

默认记录 request id、route、latency、provider/model、tool name、error class。默认不
记录完整 prompt、history、新闻正文、tool arguments 和任何 token。

### 交易安全

- Gateway 只返回 decision support；
- 不增加 `/orders`、cancel、position mutation；
- `approved=true` 仍不代表自动执行；
- UI 必须保留延迟行情和非投资保证提示。

## 9. 部署建议

建议独立 systemd unit：

```text
trade-agent-gateway.service
  WorkingDirectory=/opt/trade_agent
  ExecStart=uv run agent-tools gateway --host 127.0.0.1 --port 8010
  Restart=on-failure
```

反向代理示意：

```nginx
location /agent-api/ {
    proxy_pass http://127.0.0.1:8010/;
    proxy_read_timeout 120s;
}
```

示例只是设计方向；实际配置必须进入 `quant_trade` 独立 OpenSpec，并覆盖 auth、
header forwarding、timeout、body limit 和 failure behavior。

Gateway 故障不能阻止 Rust 行情服务启动，产品应降级为“AI 分析暂不可用”，而不是
整个行情页面不可用。

## 10. 分阶段实施

### 阶段 0：冻结 contract

- 保存现有 `/agent/analyze` request/response fixtures；
- 定义新 REST schemas、error envelope、capabilities version；
- 定义 parity 指标和回滚开关。

### 阶段 1：Gateway facade

- TDD 实现 `/health`、`/v1/capabilities`；
- TDD 实现 ContextCollector；
- `/v1/analyze` 先走 LegacyAnalysisProvider；
- `/v1/chat` 复用现有有界 agent loop。

当前状态（2026-09-01）：本阶段已在独立仓库完成并通过 in-process contract tests；
legacy provider 现在只保留为显式回滚，不再是默认路径。

### 阶段 2：产品接入

- Rust 定时 consumer 调用 `/v1/analyze`、验证 layered contract 并自行持久化；
- 停止旧 backend_llm auto pipeline 自启动；
- 保留 Gateway 配置级 legacy 回滚。

当前状态（2026-09-01）：Rust 定时 consumer 与产品持久化路径已接入；nginx/前端直接
交互不是该后台分析路径的前置条件。

### 阶段 3：native analyze

- 使用 ContextCollector 的 server-owned facts；
- 强制 structured tool/schema 并验证 action、confidence 和输出层级；
- 默认切换 native，legacy 只作显式回滚；
- 不实现、不广告不完整的 shadow。

当前状态（2026-09-01）：本阶段已在本仓库实现并通过 consumer fixture compatibility、
failure mapping 和完整回归测试。

### 阶段 3.5：异步 enrichment

- 当前已实现四类同步 contract v1 producer 和 provider-neutral structured output；
- `quant_trade` 后续提供 durable job claim/result ingestion API；
- agent worker 通过版本化 HTTP claim 和回写，不直连 PostgreSQL；
- job 增加 idempotency key、lease、retry budget 和 dead-letter 状态；
- 同步 endpoint 继续用于低吞吐调用、contract test 和 worker application core。

### 阶段 4：切换与退役

- 观察 native release，legacy fallback 保留一个 release；
- wish interpretation 已完成；Twitter 保持 raw connector + shared enrichment 架构；
- 最后在 `quant_trade` 独立 MR 删除 superseded agent code。

## 11. 验收门禁

开始切产品流量前至少满足：

- Gateway contract/auth/failure tests 全绿；
- Python/TypeScript 原有全套测试不回退；
- no-secret pack/deploy audit；
- legacy fixture contract tests；
- partial upstream failure 不编造数据；
- benchmark 默认不可被 chat 触发；
- feature flag 和配置级 rollback 都验证；
- 如果未来启用 shadow，parity 必须达到事先定义阈值；
- dsh 是否稳定与产品 Gateway 上线互不阻塞。

## 12. 最终建议

当前已经完成 **Gateway facade → Rust consumer → native analyze → wish interpretation → code
review/respond** 的解耦链路。
近期应保留 `TRADE_AGENT_ORCHESTRATION_MODE=legacy` 作为一个 release 的回滚开关，同时
观察 native 错误率和输出质量；下一步按独立契约实现 durable enrichment worker/job，
而不是让 agent 直连产品数据库、持有 GitLab token 或获得交易执行能力。
