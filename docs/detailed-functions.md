# 详细功能说明

## 1. 统一调用面

12 个 canonical tools 在不同入口保持相同业务含义：

| 入口 | 工具命名 | 适用场景 |
|---|---|---|
| Python CLI | `quote`、`kline` 等 | shell、脚本、调试、薄适配器 |
| MCP v2 | `quote`、`kline` 等 | Codex、Claude Code、Cursor 等 MCP client |
| pi extension | `quant_quote`、`quant_kline` 等 | pi 原生 tool UI 与生命周期 |
| dsh adapter | `quant_quote`、`quant_kline` 等 | 实验性 Cordis `ctx.tools` plugin |
| standalone chat | 模型自动选择 canonical tool | 不依赖 harness 的单轮多模型分析 |

所有入口最终进入 Python `ToolRegistry` 和 `QuantTradeClient`。TypeScript adapter 不实现行情、指标、信号、策略或风控算法。

## 2. 工具总览

| Tool | 输入 | 默认值 | 上游 endpoint | 副作用 |
|---|---|---|---|---|
| `quote` | `symbol` | `9984.T` | `GET /api/quote` | 无 |
| `kline` | `symbol`, `interval`, `count` | `9984.T`, `5m`, `100` | `GET /api/kline` | 无 |
| `signals` | `symbol` | `9984.T` | `GET /api/signals` | 无 |
| `news` | `count` | `10` | `GET /api/intel/news` | 无 |
| `sentiment` | 无 | — | `GET /api/intel/sentiment` | 无 |
| `trending` | `symbol` | `9984.T` | `GET /api/trend` | 无 |
| `backtest` | `symbol`, `strategy`, `interval`, `days`, `initial_cash?`, `risk_params?` | `9984.T`, `5m`, `60`, `{}` | `POST /api/backtest/historical` | 上游可能缓存 K 线并保存回测记录 |
| `benchmark` | `symbol`, `strategy`, `interval`, `top`, `initial_cash?`, `risk_params?` | `9984.T`, `5m`, `20`, `{}` | `POST /api/backtest/benchmark` | 高成本计算，最长等待 30 分钟 |
| `analyze` | `symbol`, `question?` | `9984.T`, 无 | `POST /v1/analyze` | Gateway 收集事实并调用模型，消耗模型配额 |
| `conversation_create` | `channel`, `symbol`, `title?` | `chat`, `9984.T` | `POST /api/conversations` | 创建当前认证用户的产品会话 |
| `conversation_context` | `thread_id` | 无 | `GET /api/conversations/:id/context` | 无 |
| `conversation_append` | `thread_id`, `role`, `content` | 无 | `POST /api/conversations/:id/messages` | 追加当前用户会话消息 |

所有工具都是交易决策支持工具，不会调用 `/api/orders`、撤单接口或任何券商执行能力。

## 3. 行情与情报工具

### 3.1 `quote`

用途：读取 `9984.T` 或 `6981.T` 最新行情快照。价格单位为 JPY，实际字段由上游 quote
contract 决定，通常包含当前价、涨跌、成交量、日内高低等。

```bash
uv run agent-tools quote
uv run agent-tools quote --symbol 6981.T
```

适合在任何分析开始前获取当前价格；模型不得自行编造实时价格。

### 3.2 `kline`

输入：

- `interval`：上游当前支持 `1m`、`5m`、`15m`、`1h`、`1d`、`1wk`。
- `count`：返回最新多少根 candle，范围 `1..400`。
- `symbol`：只允许 `9984.T` 或 `6981.T`。

```bash
uv run agent-tools kline --symbol 6981.T --interval 5m --count 100
```

client 将 `symbol` 与 `interval` 作为 query 发送，并在收到完整响应后保留最后 `count` 根
candle，从而维持稳定的公开工具契约。

### 3.3 `signals`

用途：读取 `quant_trade` 当前生成的交易信号集合。信号算法、强度、描述和时间信息由上游 Rust 服务计算，本仓库只转发结构化结果。

```bash
uv run agent-tools signals --symbol 6981.T
```

市场 regime 不在该 endpoint 内；需要 regime、ADX 或 RSI 时调用 `trending`。

### 3.4 `news`

输入 `count=10`，读取产品侧最近的全局新闻/社交情报，常见字段包括标题、发布者、链接、
时间、语言、来源类型与情感分数。该上游目前不按 symbol 隔离，因此工具不提供 `symbol` 参数。

```bash
uv run agent-tools news --count 20
```

上游返回 JSON array；agent-tools 统一包装为：

```json
{"articles": [{"title": "...", "sentiment_score": 0.2}]}
```

这样 CLI、MCP 和不同 harness 始终接收 JSON object。

### 3.5 `sentiment`

用途：读取上游对近期新闻和社交情报的全局聚合结果。常见内容包括 `[-1, 1]` 的聚合分数、
标签、样本量以及 bundled analysis。该接口不宣称是单一标的情感。

```bash
uv run agent-tools sentiment
```

它是事实数据的聚合，不等于未来涨跌保证。

### 3.6 `trending`

用途：读取当前趋势上下文，包括 market regime、ADX、`+DI/-DI`、RSI、均线斜率与布林带宽等上游可用字段。

```bash
uv run agent-tools trending --symbol 6981.T
```

推荐与 `quote`、`signals`、`sentiment` 联合使用，而不是单独把单个指标解释为买卖指令。

## 4. 策略计算工具

### 4.1 `backtest`

```bash
uv run agent-tools backtest \
  --symbol 6981.T --strategy vwap --interval 15m --days 90 \
  --initial-cash 1000000 --risk-params '{"max_drawdown": 0.1}'
```

公开输入保持简洁的 strategy ID，并将 `symbol`、字符串 `strategy`、`interval`、`days`、
`risk_params` 和可选 `initial_cash` 原样映射到产品 HTTP contract。本仓绝不展开或维护策略
默认参数；默认值只由 Rust `StrategyConfig::default_for_id` 解析，未知 ID 由 producer fail
closed。

支持的 strategy ID：`ma_cross`、`rsi`、`bb`、`vwap`、`volume`、`combined`、`macd`、
`pivot`、`mfi`、`linreg`、`logistic`、`knn`、`sentiment_combo`。

产品 `v1.5.62` 已部署字符串 ID 或完整 config 的兼容输入，bounded production smoke 已验证
string-ID historical 返回成功。产品 `v1.5.63` 已部署 optimizer starvation hotfix，并在 optimizer
运行期间通过产品侧重复 health/quote 稳定性检查；readiness gate 已满足。

结果由上游 `BacktestResult` 定义，通常包含策略名、收益率、年化收益、最大回撤、Sharpe、胜率、盈亏比、交易次数和交易明细。历史回测可能把结果保存到上游 `backtest_runs`，但不会触发真实订单。

### 4.2 `benchmark`

```bash
uv run agent-tools benchmark \
  --symbol 6981.T --strategy rsi --interval 1h --top 10 \
  --initial-cash 1000000 --risk-params '{"max_drawdown": 0.1}'
```

上游 benchmark 会扫描多个策略族和参数组合，而不是接受单一 strategy。agent-tools 的 normalization 流程为：

1. 发送 `symbol`、`interval`、`risk_params`、可选 `initial_cash` 与
   `use_history=true`，启动上游全量扫描。
2. 等待上游返回完整排序结果。
3. 按 `strategy_id` 过滤。
4. 只返回前 `top` 条，并把该集合第一条设为公开 `best_overall`。

可扫描策略为：`ma_cross`、`rsi`、`bb`、`volume`、`combined`、`macd`、`mfi`、`linreg`、`logistic`、`knn`、`sentiment_combo`。上游当前不扫描 `vwap` 和 `pivot`，因此 schema 不允许把它们传给 benchmark。

该调用在生产数据上可能需要 5–10 分钟，HTTP 与 pi/dsh adapter timeout 均设置为 30 分钟。

## 5. Native 分析工具

### 5.1 `analyze`

输入及默认值：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `symbol` | `9984.T` | 标的代码 |
| `question` | 无 | 最多 2000 字符的可选分析问题 |

```bash
uv run agent-tools analyze --symbol 6981.T --question '说明主要风险'
```

CLI 只向 Intelligence Plane Gateway 发送 `symbol`、可选 `question` 与固定
`mode=standard`。价格、RSI、ADX、regime 和情感都由 Gateway 从产品 HTTP API 收集，
不接受 harness 伪造的实时事实。结果为 `facts/analysis/decision/provenance/warnings`
layered contract，只供决策支持。

### 5.2 产品会话工具

`conversation_create`、`conversation_context` 与 `conversation_append` 通过认证 HTTP 调用
`quant_trade` 的 Conversation API。它们不访问数据库文件，也不在本仓保存 session。多个
harness 使用同一个产品用户凭据与 thread ID 时，可以读取和追加同一会话上下文。

create 的 channel 只允许 `chat|wish`，symbol 只允许 `9984.T|6981.T`；context 只读，append
只允许 `user|assistant` 且 content 最多 8000 字符。所有权与最终长度校验仍由产品 API 执行。

## 6. 独立多模型 Agent

`chat` 在没有 harness 时提供一个有界 OpenAI-compatible tool-calling loop：

```text
用户问题
  → provider chat/completions
  → 模型选择一个或多个 canonical tool
  → ToolRegistry 执行并回灌 JSON
  → 模型生成最终简体中文回答
  → 超过 max_iterations 则失败，不无限循环
```

provider、model 与 credential 由部署环境注入，不在公开文档中给出值；使用方法见
`agent-tools chat --help`，可用字段见 `.env.example`。模型只负责规划和解释；真实数值必须
来自工具。

## 7. REST Agent Gateway

Gateway 是可选安装的产品 REST 边界，不替代 MCP。MCP 面向 harness；Gateway 面向
`quant_trade` Web UI、后端服务和需要稳定 HTTP contract 的调用方。

### 7.1 启动与配置

```bash
uv sync --extra gateway
uv run agent-tools gateway --host 127.0.0.1 --port 8010
```

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| `TRADE_AGENT_API_TOKEN` | 空 | 非空时保护除 `/health` 外的所有路由 |
| `TRADE_AGENT_ORCHESTRATION_MODE` | `native` | `native` 默认；`legacy` 为显式回滚；未实现的 `shadow` 会拒绝启动 |
| `TRADE_AGENT_MAX_HISTORY` | `20` | `/v1/chat` 最大历史消息数 |

Gateway 默认只监听 loopback。生产部署推荐由 nginx 同源反代，不把 provider key、
`QUANT_TRADE_API_TOKEN` 或内部端口暴露给浏览器。

### 7.2 `/v1/analyze`

请求只接受 `symbol`、可选 `question` 和 `mode=standard`；Pydantic 使用
`extra=forbid`，所以调用方传入 `price/rsi/adx/sentiment` 会得到 422，而不会污染事实。

ContextCollector 通过同一 `ToolRegistry` 并行调用六类来源：

1. `quote` 提取当前价格；
2. `kline(interval=5m,count=100)` 提取最后一个有效 `rsi14`；
3. `trending` 提取 regime 与 ADX；
4. `signals` 保留当前量化信号事实；
5. `sentiment` 提取聚合新闻情感；
6. `news(count=50)` 提取 Twitter 样本情感与数量。

非关键来源失败会进入 `warnings` 和 source status；缺少价格、regime、ADX、RSI 或新闻
情感时返回可重试的 `CONTEXT_INCOMPLETE`，绝不补造默认事实。默认
`NativeAnalysisProvider` 只把 snapshot 的 facts/derived 送入强制
`record_native_analysis` tool schema，并把严格校验后的模型字段规范化为：

```text
facts / analysis / decision / provenance / warnings
```

模型只能返回 `summary`、`trend_direction`、`action`、`confidence`、`approved` 和
`risk_notes`。action 仅允许 `BUY/HOLD/SELL`，confidence 必须是有限的 `[0,1]`，任何未知
字段、错误枚举、空文本或类型强制转换都返回 `MODEL_RESPONSE_ERROR`。facts、as-of、成功
tools 和 source warnings 始终由服务端 snapshot 决定。结果仅供决策支持，不存在
order/cancel/broker mutation。

显式设置 `TRADE_AGENT_ORCHESTRATION_MODE=legacy` 可回滚到既有
`POST /agent/analyze` adapter；默认 native 路径不会调用该 endpoint。

### 7.3 `/v1/chat`

Chat 是无状态的：调用方每次显式传入 `history` 与可选 `context_summary`，Gateway 只用于当前请求且不持久化。
`context_summary` 以 JSON 封装的 user-role 不可信数据传入，不会创建第二条 system message。
模型继续使用同一个 `OpenAICompatibleAgent` 和 canonical registry。默认从 registry 删除
`benchmark`；只有 `allow_expensive_tools=true` 才把它提供给模型。三个 product-owned conversation
工具也不会进入 Gateway 内部 agent loop，避免模型使用服务端凭据读写会话。任何情况下都不存在
order、cancel 或持仓修改工具。

### 7.4 `/v1/summarize/conversation`

摘要 producer 接受可选旧摘要与有界、按顺序排列的 `user|assistant` 消息，通过 forced
structured output 返回简体中文非空摘要。输入只作为不可信数据，不得改变系统任务或授权工具。
该 endpoint 不调用行情工具、不持久化、不访问产品数据库；summary watermark、保留窗口和
重试策略都由 `quant_trade` 管理。

### 7.5 Contract v1 intelligence producer

四类同步 producer endpoint 复用 `GatewayIntelligenceService`、`resolve_provider()` 和
OpenAI-compatible forced function/tool call：

| Endpoint | 输入要点 | 输出约束 |
|---|---|---|
| `/v1/enrich/headlines/sentiment` | 唯一整数 ID、标题、语言，最多 100 条 | score clamp 到 `[-1,1]`；只能返回请求 ID 子集；缺失项只 repair 一次 |
| `/v1/enrich/sentiment-summary` | 多语言标题与 price context | 有界 score/枚举；`article_count`、`analyzed_at` 由服务端生成 |
| `/v1/narratives/gap` | gap 百分比与来源标题 | 简体中文非空、最多 60 字，拒绝明显后市预测/交易建议 |
| `/v1/translate` | text、source language、`target_language=zh-CN` | 只返回非空翻译文本 |

所有请求禁止额外字段。成功响应统一含：

```json
{
  "request_id": "...",
  "contract_version": "v1",
  "provenance": {"provider": "...", "model": "..."},
  "warnings": []
}
```

模型返回未知/重复 headline ID、非有限 score、错误枚举、空文本或不符合 schema 时返回
`MODEL_RESPONSE_ERROR`，不会把错误包装成中性结果。默认实现不访问 `quant_trade` HTTP API
或数据库；未来 MCP/worker 应复用该 application service。

Producer OpenAPI snapshot 位于 `openapi/agent-gateway-v1.json`。

### 7.6 错误与认证

每个响应包含 `X-Request-ID`；成功分析/chat 也在 JSON 中返回同一 request id。错误统一为：

```json
{
  "error": {
    "code": "CONTEXT_INCOMPLETE",
    "message": "...",
    "request_id": "...",
    "retryable": true
  }
}
```

配置 `TRADE_AGENT_API_TOKEN` 后使用 Bearer 认证，并在任何行情、工具或模型调用前拒绝
无效请求。未知内部异常返回不含原始异常信息的 `INTERNAL_ERROR`。

### 7.7 `/v1/interpret/wish`

请求严格只接受：

```json
{
  "message": "增加多周期K线切换",
  "history": [{"role": "user", "content": "我想改进K线图"}]
}
```

message 与每条 history content 最多 8000 字符且不能是空白；history 最多 20 条，role 只允许
`user|assistant`。请求不接受 issue body、GitLab project/token 或任何 mutation 参数。

Gateway 把有序完整 history 与当前 message 发送给 forced
`record_wish_interpretation` structured tool。phase 规则：

| Phase | 结构要求 |
|---|---|
| `clarifying` | 可省略结构字段，reply 必须继续询问缺失信息 |
| `confirming` | 必须完整返回 title/type/priority/requirements/summary |
| `confirmed` | 必须从 history 重建并再次返回同一份完整 validated payload |

type 仅允许 `feature|bug|refactor`；priority 仅允许 `low|medium|high|urgent`。reply、title、
summary 与 requirements 使用简体中文并分别执行长度/非空检查。unknown keys、bare confirmed
phase、空 requirements 或恶意枚举返回 `MODEL_RESPONSE_ERROR`，不会伪造成确认成功。

成功响应包含 `request_id`、`contract_version=v1`、`reply`、`wish`、provider/model
provenance 和 warnings。本仓库没有 GitLab client 或 token，也不创建 issue；产品侧只有在
收到 `phase=confirmed` 的完整 payload 后才能执行自己的 issue mutation。

### 7.8 `/v1/review/code`

请求严格只接受 `diff` 与可选 `project_context`：diff 必须非空且最多 120000 字符，context
若提供必须非空且最多 20000 字符。Gateway 使用共享 `StructuredModelExecutor` 强制调用
`record_code_review` schema，模型只能返回：

```json
{
  "review": "有界评审文本",
  "verdict": "NEEDS_CHANGES"
}
```

review 必须非空且最多 12000 字符；verdict 只允许 `LGTM|NEEDS_CHANGES`。未知字段、空文本、
错误枚举或超长值返回 `MODEL_RESPONSE_ERROR`。diff/context 始终是不可信数据，不能改变系统
任务或触发命令、工具、代码修改及外部 mutation。

### 7.9 `/v1/review/respond`

请求严格只接受非空且最多 8000 字符的 `message` 与可选、非空且最多 20000 字符的
`context`。forced `record_review_response` schema 只接受一个非空、最多 8000 字符的 `reply`。

两个 review endpoint 的成功响应都包含 `request_id`、`contract_version=v1`、provider/model
provenance 和 warnings。它们无状态、不读写 GitLab/数据库/仓库、不执行 coding-agent loop；
quant-core 只需固定 OpenAPI snapshot、传入文本并消费响应。

## 8. 错误与安全语义

- HTTP 4xx/5xx 原样作为失败暴露，不伪造成功结果。
- 非预期 JSON shape 会明确报错，防止模型把错误页面当行情。
- 未支持的 symbol、interval 或 strategy 在发送网络请求前拒绝。
- benchmark 与 agent loop 均有上限：前者 30 分钟，后者最大工具迭代次数。
- API token 和模型 key 只从环境变量读取。
- 所有发布工具都没有 order/cancel/live-strategy mutation。

## 9. 当前限制

- 六个 market/backtest 工具及 Gateway analyze/chat 已支持 `9984.T|6981.T`。
- 新闻与聚合情感仍是全局源，不按 symbol 隔离。
- 字符串 strategy ID 已在产品 `v1.5.62` 通过 bounded smoke；产品 `v1.5.63` optimizer hotfix
  也已通过运行中稳定性验收。
- Yahoo Finance 免费行情可能延迟约 15 分钟。
- pi 尚待干净安装环境 E2E；dsh 尚待固定版本真实 harness E2E。
- benchmark 是同步长任务；未来可在上游提供 job/progress contract 后改为异步工具。
- 当前 TypeScript schema 是受测试保护的 snapshot；未来可从 Python canonical schema 自动生成。
- Gateway analyze 已默认 native；legacy 仅为显式回滚，shadow 不实现也不广告。Gateway 会话
  始终无状态；持久会话由产品 Conversation API 实现。durable enrichment jobs 与剩余 Twitter
  orchestration 仍未实现。
