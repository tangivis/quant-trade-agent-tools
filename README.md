# quant-trade-agent-tools

面向 `9984.T` 与 `6981.T` 的独立、可扩展、多 harness、多模型 agent 工具仓库。

本仓库是完整的 **Intelligence Plane**：拥有 provider adapters、prompts、structured model
execution、agent orchestration、REST/MCP/CLI 和薄 harness adapters。独立的 `quant_trade` 是
**Product/Data/Domain Plane**：拥有事实、确定性交易域逻辑、持久化、产品 UI/API、风控与执行
边界。两者是通过版本化 HTTP contract 协作的同级服务，不存在源码继承或共享数据库关系。

公开架构与安全策略分别见 [ARCHITECTURE.md](ARCHITECTURE.md) 和
[SECURITY.md](SECURITY.md)。

公开入口：[GitHub](https://github.com/tangivis/quant-trade-agent-tools) ·
[Pages（合并后上线）](https://tangivis.github.io/quant-trade-agent-tools/) ·
[PyPI（首次 Trusted Publishing 后可用）](https://pypi.org/project/quant-trade-agent-tools/)

本仓库不复制 `quant_trade` 的行情、信号、回测或 LangGraph 业务实现，也不依赖它的 Python 包和数据库；所有业务数据只通过 `quant_trade` 已发布 HTTP API 获取。因此它可以独立版本化、测试、发布并安装到 pi、MCP harness 或未来平台。

> 定位是行情分析与交易决策支持，不是券商执行器。没有下单、撤单或自动实盘工具。价格单位为 JPY，免费行情可能约有 15 分钟延迟。

## 项目状态

| 项目 | 状态 | 说明 |
|---|---|---|
| 当前 release candidate | `0.4.0` | 会话上下文、native analyze 工具边界与公开发布加固；尚未 tag、publish 或 deploy |
| 独立 Git 仓库 | ✅ | 与 `quant_trade` 并列，拥有独立版本、CI 和发布物 |
| GitHub Pages | 待当前 PR 合并 | 仅发布 allowlisted `site/`，不发布内部执行文档 |
| PyPI | 待 Trusted Publisher | OIDC opt-in；不保存长期 PyPI token |
| Python CLI | 可用 | 12 个 canonical tools + `mcp` + `chat` + `gateway` |
| MCP v2 | ✅ | stdio 与 Streamable HTTP，结构化输出和副作用 annotations |
| REST Agent Gateway | ✅ Contract v1 producer | native analysis、chat、enrichment、wish 与无副作用 code review/respond |
| 多模型 runtime | ✅ | GPT、DeepSeek、Kimi、MiniMax、Ollama、custom |
| pi extension | ✅ 本地验证 | 单测、typecheck、bundle、npm pack 已通过；待干净环境安装 E2E |
| dsh adapter | ⚠️ Experimental | 官方 plugin/tool/bundle 形态已通过单测、类型与 Node smoke；待固定 dsh 版本真实加载 E2E |
| 券商实盘执行 | ❌ 不提供 | 无下单、撤单、持仓修改工具 |

### Release 状态

版本 tag 的 **source/artifact release** 与公共 registry publication 是两个独立状态。合法 tag
通过全量门禁后，CI 总会构建并保留 Python sdist/wheel 与 pi/dsh npm tarball；这不需要 PyPI
或 npm credential，也不表示包已发布到公共 registry。

PyPI/npm publication 是显式 opt-in：只有对应 enable flag 与受保护 credential 同时存在时，
相应 job 才消费已保留的 artifact；否则 job skipped，文档和 release 状态不得写成 published。
dsh 即使允许 npm publication 也仍使用 experimental dist-tag。完整操作和未来
OIDC/trusted-publishing 建议见 `docs/agent-tools-publish.md`。

公开 GitHub pull request 通过仓库自带的凭据无关 CI 独立验证：锁定依赖后运行 Python/TypeScript
测试、Ruff、类型检查、bundle、sdist/wheel 与 npm dry-run。工作流仅授予 `contents: read`，所有
外部 action 固定到完整 commit SHA，并且不会启用真实 provider smoke 或 registry publication。

## 当前能力

- 12 个 canonical tools：9 个行情/分析工具，以及 `conversation_create`、`conversation_context`、`conversation_append` 三个产品会话工具。
- `quote/kline/signals/trending/backtest/benchmark` 使用严格的 `9984.T|6981.T` symbol
  enum；上游新闻与聚合情感仍是全局源，不伪装为按 symbol 隔离。
- Python CLI：人类、脚本和薄适配器共用同一工具契约。
- 真实 MCP v2 server：支持 `stdio` 与 `streamable-http`，可接 Codex、Claude Code、Cline、Roo、Continue、Cursor 等 MCP client。
- pi npm extension：注册 `quant_*` tools，已通过单元测试与构建。
- DeepSeek Harness/Cordis adapter：使用 `apply`/`inject`、`ctx.tools.register()` 与 `dsh.bundle` patch；因尚无真实 profile E2E，仍明确标记为 experimental。
- 可选独立 model runtime：通过 OpenAI-compatible Chat Completions 接 GPT、DeepSeek、Kimi、MiniMax、Ollama 或自定义网关。
- 可选 REST Agent Gateway：提供稳定 v1 contract、Bearer 鉴权、request id、服务端行情上下文、native layered analysis、四类 enrichment、无状态 chat/wish、会话摘要和无副作用 code review/respond API。
- SDD + TDD：仓库级规则见 `AGENTS.md`，本次规格见 `openspec/changes/standard-multi-harness-agent/`。

## 架构

```text
pi extension ─┐
dsh adapter ──┼─> CLI / canonical tool registry ─> quant_trade HTTP APIs
scripts ──────┘                  │
                                ├─> MCP v2 server ─> any MCP harness
                                ├─> optional OpenAI-compatible agent loop
quant_trade Web UI ─> nginx ────└─> optional REST Agent Gateway
                                           ├─> canonical market tools
                                           ├─> provider-neutral native analyze
                                           ├─> native /v1/analyze (canonical tool target)
                                           ├─> model-driven enrichment APIs
                                           ├─> stateless wish interpretation
                                           └─> stateless code review/respond

quant_trade API:   QUANT_TRADE_API_URL   (默认 http://127.0.0.1:5188)
Intelligence Gateway: QUANT_TRADE_GATEWAY_URL (默认 http://127.0.0.1:8010)
```

Harness 通常拥有自己的模型，此时只需要 MCP 或对应 adapter，不需要配置本仓库的模型。只有直接运行 `chat` 时，才需要模型 endpoint 和 key。

核心分层：

1. `QuantTradeClient`：适配并规范化上游 Rust/Python HTTP API。
2. `ToolRegistry`：定义 12 个稳定工具名、输入 schema、默认值和 dispatch。
3. CLI/MCP：面向脚本与通用 harness 的稳定协议。
4. pi/dsh：只做注册、参数序列化和结果回传，不含交易算法。
5. standalone agent：可选的有界 tool-calling loop，harness 自带模型时不启用。

## 安装与开发

```bash
cd quant-trade-agent-tools

uv sync --extra dev
bun install

cp .env.example .env
uv run agent-tools quote
```

服务地址可以分别配置：

```bash
export QUANT_TRADE_API_URL=http://127.0.0.1:5188
export QUANT_TRADE_GATEWAY_URL=http://127.0.0.1:8010
export QUANT_TRADE_AGENT_TOKEN=<injected-by-secret-store>
```

认证凭据应由部署平台的 secret store 注入，不在公开文档、shell history 或浏览器配置中展示。

## REST Agent Gateway

Gateway 是给 `quant_trade` Web UI、服务端应用或其他非 MCP 调用方使用的可选产品接口。它不会让浏览器提交价格、RSI、ADX 或情感分数作为权威事实；`/v1/analyze` 会在服务端并行读取 `quote`、`kline`、`signals`、`news`、`sentiment`、`trending`，再通过 provider-neutral forced structured call 生成 layered decision support。默认路径不再调用 legacy Python `/agent/analyze`。

四个 contract v1 intelligence endpoint 使用同一个 provider-neutral application service 和
OpenAI-compatible forced tool-call client。它们不读取产品数据库，也不 import
`quant_trade`；调用方负责通过版本化结果 API 持久化 enrichment。

`/v1/interpret/wish` 复用同一 structured model boundary，只解释完整的当前 message/history。
本仓库不持有 GitLab token、不创建 issue；只有 `quant_trade` 在收到完整 validated
`phase=confirmed` payload 后执行产品侧 mutation。

`/v1/review/code` 与 `/v1/review/respond` 同样复用 provider-neutral forced structured boundary。
provider、prompt 和 schema 全部保留在本仓；产品只提交有界文本并消费结果。diff/context 被视为
不可信数据，producer 不运行本地 coding agent、不操作仓库/GitLab/数据库，也不执行交易动作。

`/v1/chat` 接受产品组合的 `context_summary`、近期 history 和已校验 symbol，但不保存会话。
摘要与 symbol 始终以不可信 user-role 数据传入模型，不会升格为 system instruction。若模型在
symbol-scoped 工具调用中省略 symbol，runtime 才补入该已校验值；显式参数保持不变，全局
news/sentiment 不会被伪装成按 symbol 隔离。`/v1/summarize/conversation` 把旧摘要和有界消息压缩
为新的简体中文摘要，同样不访问产品数据库。长期消息、用户所有权、thread/channel/symbol 由
`quant_trade` 的 Conversation API 和 PostgreSQL 管理。

```bash
uv sync --extra gateway
uv run agent-tools gateway --host 127.0.0.1 --port 8010
```

公开 liveness 不调用行情或模型：

```bash
curl http://127.0.0.1:8010/health
```

其余 v1 路由需要由服务端认证层验证 Bearer 凭据；具体凭据值和生产地址不属于公开配置。
请求与响应结构以 `openapi/agent-gateway-v1.json` 为准。

| 路由 | 行为 |
|---|---|
| `GET /health` | 仅进程存活检查，不调用上游 |
| `GET /v1/capabilities` | 返回 v1、工具、provider、symbol、transport 和当前编排模式 |
| `POST /v1/analyze` | 服务端收集事实，native provider 输出 facts/analysis/decision/provenance/warnings |
| `POST /v1/chat` | 使用调用方提供的有界历史；默认移除 `benchmark`，显式 allow 才开放 |
| `POST /v1/enrich/headlines/sentiment` | 批量标题 score、ID 子集校验和最多一次 missing-ID repair |
| `POST /v1/enrich/sentiment-summary` | 多语言聚合情感；article count/时间戳由服务端生成 |
| `POST /v1/narratives/gap` | 最多 60 字、无展望或交易建议的简体中文事实叙事 |
| `POST /v1/translate` | 把指定源语言文本翻译为 `zh-CN` |
| `POST /v1/interpret/wish` | 无状态愿望澄清/确认；confirmed 必须从 history 重建完整 payload |
| `POST /v1/review/code` | 评审有界 diff/context，返回 review 与 `LGTM|NEEDS_CHANGES` |
| `POST /v1/review/respond` | 根据有界 message/context 生成无副作用 review reply |
| `POST /v1/summarize/conversation` | 把旧摘要与有界消息压缩为新的无状态会话摘要 |

`GET /v1/capabilities` 的 `intelligence_tasks` 只列出已实现能力。producer contract 固定在
`openapi/agent-gateway-v1.json`；consumer 应固定该 snapshot 并执行 compatibility tests。

`TRADE_AGENT_ORCHESTRATION_MODE` 默认是 `native`。紧急回滚可显式设为 `legacy`，该路径使用
独立的产品 legacy client method，绝不回调本 Gateway 的 native `/v1/analyze`；`shadow`
尚未实现，配置时会启动失败，也不会出现在 capabilities 的 available/planned 中。
`quant_trade` 当前由 Rust 定时调用 `/v1/analyze` 并自行持久化结果；本仓库仍不读产品 DB。
wish consumer 与产品侧 GitLab issue 创建由 `quant_trade` 持有。durable worker/job 和剩余
Twitter orchestration 不在本切片内。

## MCP

本地启动 stdio MCP server：

```bash
uv run agent-tools mcp
```

以 Streamable HTTP 启动：

```bash
uv run agent-tools mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

通用 MCP client 配置示例：

```json
{
  "mcpServers": {
    "quant-trade": {
      "command": "uvx",
      "args": [
        "quant-trade-agent-tools",
        "mcp"
      ]
    }
  }
}
```

不同 harness 的配置文件位置不同，但 command/args 协议相同。

## pi 与 dsh

pi 发布包：

```bash
pi install npm:@quant-trade/agent-tools-pi
```

当前 peer contract 为 pi `0.84.x`。发布 adapter 使用 Node.js subprocess API；Bun 仅用于本仓库开发、测试和 bundle 构建，不是 pi 运行时依赖。机器上仍需安装 `uv`，并保证 `uvx quant-trade-agent-tools` 能运行且可访问 `quant_trade` HTTP 服务。

开发目录可直接构建：

```bash
bun run build
```

dsh adapter 位于 `packages/agent-tools-dsh/`，通过当前 bundle/profile 安装机制接入：

```bash
dsh plugin --profile <profile> add @quant-trade/agent-tools-dsh@experimental
```

当前类型检查目标为 Cordis `4.0.x` 与 `@deepseek-ai/dsh-tools 0.1.1-rc.2`。插件使用 `ctx.tools.register()` 暴露 12 个 `quant_*` 工具并转发 harness cancellation signal；但在固定 dsh profile 完成真实加载、工具发现和调用 E2E 之前，不视为完整兼容或可上架稳定版。

## 多模型独立运行

runtime 支持多个 OpenAI-compatible provider adapter 与显式 custom 配置。部署者在 secret
store 和受控运行配置中选择 provider、model 与凭据；这些值不得写入公开文档、浏览器配置或
产品运行时。可用配置字段见 `.env.example`，命令选项见 `agent-tools chat --help`。

## 工具边界

| Tool | 主要输入 | 上游服务 | 公开结果/处理 |
|---|---|---|---|
| `quote` | `symbol=9984.T` | `GET /api/quote` | 支持标的的最新行情对象 |
| `kline` | `symbol, interval=5m, count=100` | `GET /api/kline` | 只保留最新 `count` 根 K 线 |
| `signals` | `symbol=9984.T` | `GET /api/signals` | 支持标的的当前策略信号集合 |
| `news` | `count=10` | `GET /api/intel/news` | 上游数组规范化为 `{articles: [...]}` |
| `sentiment` | 无 | `GET /api/intel/sentiment` | 近时段聚合情感及样本信息 |
| `trending` | `symbol=9984.T` | `GET /api/trend` | regime、ADX、DI、RSI 等趋势上下文 |
| `backtest` | `symbol, strategy, interval, days, initial_cash?, risk_params?` | `POST /api/backtest/historical` | 原样转发 strategy ID；不在本仓解析默认参数 |
| `benchmark` | `symbol, strategy, interval, top, initial_cash?, risk_params?` | `POST /api/backtest/benchmark` | 高成本全量扫描后按策略过滤并限制结果数 |
| `analyze` | `symbol, question?` | `POST /v1/analyze` | Gateway 收集服务端事实并返回 layered decision support |
| `conversation_create` | `channel, symbol, title?` | `POST /api/conversations` | 创建当前认证用户的产品会话 |
| `conversation_context` | `thread_id` | `GET /api/conversations/:id/context` | 读取产品组合的摘要与近期消息 |
| `conversation_append` | `thread_id, role, content` | `POST /api/conversations/:id/messages` | 追加有所有权校验的消息 |

上述六个 symbol-scoped 工具只接受 `9984.T`、`6981.T`；interval 只接受
`1m|5m|15m|1h|1d|1wk`，未知值在联网前 fail closed。`news` 与 `sentiment` 当前来自产品侧
全局源，因此没有 `symbol` 参数。

历史回测合同刻意发送字符串 strategy ID（如 `"vwap"`），本仓不复制 Rust 默认参数。
产品 `v1.5.62` 已部署字符串 ID 与完整 config 的兼容解析，默认参数仍只在 Rust
`StrategyConfig::default_for_id` 中解析并拒绝未知 ID。bounded client/MCP contract smoke 已
通过；过程中发现的 CPU optimizer starvation 属于产品 runtime。产品 `v1.5.63` 已部署 hotfix，
并在 optimizer 实际运行期间通过重复 health/6981.T quote 稳定性检查。本仓 readiness gate 已
满足；MR 仍必须通过自身 pipeline/review，且不会自动 merge、tag 或 deploy。

MCP 将 6 个查询工具和 `conversation_context` 标记为只读；`backtest`、`benchmark`、`analyze`、`conversation_create`、`conversation_append` 标记为非只读但非破坏性。历史回测可能在上游保存回测记录或缓存行情，conversation 写工具会修改当前用户的产品会话，但所有工具都不会触发券商动作。

详细参数、支持的 strategy ID、输出结构、错误语义和调用示例见 `docs/detailed-functions.md`。

## 验证

```bash
uv run pytest tests/ -v
bun test packages/
bun run typecheck
bun run build
uv build
```

### Opt-in 真实 provider staging smoke

默认 `uv run pytest tests/` 不会访问真实 provider；live case 会显示 skipped。只有同时显式
启用开关并存在所选 provider key 时才会构造网络 client：

在隔离 staging 已完成 provider 配置后，可由发布操作者显式设置
`RUN_REAL_PROVIDER_E2E=1` 并运行 `uv run python -m agent_tools.staging_smoke`。

pytest 对应 live case 也受同一双门禁保护，默认 full suite 不访问网络。

runner 真实验证 provider-neutral structured executor 的 translation、wish clarifying 与 wish
confirming。stdout 只包含脱敏 JSON：provider/model category、`agent-gateway-v1`、每项 latency、phase
和 `contract_valid`；不会输出 key、base URL、prompt/history、翻译/wish 正文、provider body
或异常原文。它没有 GitLab client/token，也不调用产品 mutation、DB 或交易执行接口。若
`RUN_REAL_PROVIDER_E2E` 不是精确的 `1`，或 provider key 缺失，runner 在 service 构造前安全
skip。

已验证结果记录在 `docs/agent-tools-verification.md`。

## 文档

- `ARCHITECTURE.md`：公开的双平面职责、层级、接口与信任边界。
- `SECURITY.md`：公开的安全、隐私、凭据、日志与漏洞报告策略。
- `docs/agent-tools-multi-platform-architecture.md`：边界、扩展点和依赖方向。
- `docs/architecture/quant-trade-agent-gateway-integration.md`：`quant_trade` 调用独立 agent 的推荐架构与迁移决策。
- `docs/detailed-functions.md`：12 个工具与独立 agent runtime 的详细功能说明。
- `docs/architecture/conversation-context.md`：产品持久会话与无状态 Intelligence Plane 的边界。
- `docs/plans/2026-09-01-agent-gateway-integration.md`：Gateway 的分阶段 SDD/TDD 实施计划。
- `openspec/changes/contract-v1-intelligence-producer/`：四类 intelligence producer 的冻结行为与任务。
- `docs/plans/2026-09-01-contract-v1-intelligence-producer.md`：contract v1 producer 的红绿重构顺序。
- `openspec/changes/native-analysis-provider/`：native analyze、mode 和 layered contract 规格。
- `docs/plans/2026-09-01-native-analysis-provider.md`：第二解耦切片的 TDD 实施计划。
- `openspec/changes/wish-interpretation-producer/`：无状态 wish producer 与 mutation 边界规格。
- `docs/plans/2026-09-01-wish-interpretation-producer.md`：第三解耦切片的 TDD 实施计划。
- `openspec/changes/real-provider-staging-smoke/`：真实 provider 双门禁与脱敏报告规格。
- `docs/plans/2026-09-01-real-provider-staging-smoke.md`：staging smoke 与 snapshot parity 计划。
- `openspec/changes/code-review-producer/`：无副作用 code review/respond producer 契约。
- `docs/plans/2026-09-02-code-review-producer.md`：code review producer 红绿重构与边界审计计划。
- `openspec/changes/public-documentation-hardening/`：公开文档与敏感信息扫描规格。
- `docs/plans/2026-09-02-public-documentation-hardening.md`：公开文档红绿重构计划。
- `docs/mr/2026-09-01-contract-v1-intelligence-producers.md`：待人工创建的独立 producer MR draft。
- `openapi/agent-gateway-v1.json`：本仓库维护的 Intelligence Plane producer contract snapshot。
- `docs/agent-tools-publish.md`：发布与 harness 接入。
- `docs/agent-tools-verification.md`：测试、构建、安全和已知限制。
- `docs/migration-from-quant-trade.md`：结合原调查与 changelog 的迁移结论。

## License

MIT，见 `LICENSE`。
