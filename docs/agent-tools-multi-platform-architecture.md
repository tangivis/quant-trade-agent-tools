# 多平台 Agent 架构

本页补充 harness 与工具实现细节；公开的系统级职责、层级关系和信任边界以根目录
`ARCHITECTURE.md` 为准，隐私与凭据规则以 `SECURITY.md` 为准。

## 目标

`quant-trade-agent-tools` 是完整、独立的 Intelligence Plane，而不是 `quant_trade` 的第二份
业务实现。它拥有 provider adapters、prompts、structured execution、orchestration、REST、
MCP/CLI 与薄 harness adapters，让不同 harness 和模型复用同一组行情分析、信号、回测和
决策支持工具。独立的 Product/Data/Domain Plane 保持事实、确定性域逻辑、持久化、风险与
执行边界的唯一真相来源。

## 依赖方向

```text
Harness adapters                  Generic clients
┌────────────┐ ┌────────────┐     ┌──────────────┐
│ pi         │ │ dsh (exp.) │     │ MCP harness  │
└─────┬──────┘ └─────┬──────┘     └──────┬───────┘
      └──────────────┼────────────────────┘
                     ▼
          canonical ToolRegistry
           ┌─────────┴─────────┐
           ▼                   ▼
       Click CLI          MCP v2 server
           │                   │
           └─────────┬─────────┘
                     ▼
             QuantTradeClient
             ┌───────┴────────┐
             ▼                ▼
      Rust market API   Python agent API
          :5188              :8003
```

REST Gateway 和独立 `chat` 在工具层之上复用 provider-neutral structured execution 与有界
tool-calling。pi、dsh 或 MCP harness 已经持有模型时，不经过 standalone model loop。

## 组件职责

| 组件 | 路径 | 职责 | 不负责 |
|---|---|---|---|
| HTTP client | `src/agent_tools/client.py` | URL/auth、上游 request mapping、response normalization、timeout | 指标和策略算法 |
| Tool registry | `src/agent_tools/tools.py` | 工具名、schema、默认值、dispatch、副作用元数据 | harness 生命周期 |
| CLI | `src/agent_tools/cli.py` | 参数解析、JSON stdout、MCP/chat 入口 | 业务计算 |
| MCP server | `src/agent_tools/mcp_server.py` | MCP v2 注册、transport、structured output、annotations | 模型选择 |
| Model runtime | `src/agent_tools/agent.py` | 有界 tool-calling loop、结果回灌 | 持久会话和券商执行 |
| Provider resolver | `src/agent_tools/providers.py` | preset、环境覆盖、key 解析 | 厂商专有 SDK |
| CLI bridge | `packages/cli-bridge/` | Node child process、参数序列化、timeout/cancellation、结果解析、TS schema snapshot | 市场逻辑 |
| pi adapter | `packages/agent-tools-pi/` | `quant_*` tool 注册 | Python/HTTP 实现 |
| dsh adapter | `packages/agent-tools-dsh/` | Cordis plugin lifecycle、`ctx.tools` 注册、bundle patch | 稳定版兼容承诺 |

## 稳定核心

### `QuantTradeClient`

- 行情与计算 API：`QUANT_TRADE_API_URL`。
- 多 agent 分析 API：`QUANT_TRADE_AGENT_URL`。
- 可选 Bearer auth：`QUANT_TRADE_API_TOKEN`。
- 将上游不同 JSON shape 规范化为公开 object contract，非法 shape 显式失败。
- 对 backtest/benchmark 完成 Rust request mapping，避免 harness 感知内部 enum。
- benchmark 单请求允许 30 分钟，其余请求保持短 timeout。

### `ToolRegistry`

9 个 canonical tool 名称和 JSON schema 是跨平台兼容面的唯一真相。新增 harness 应复用 registry 或 CLI，不应重写业务映射。

### MCP v2

- `stdio` 适合本地 harness 启动子进程。
- `streamable-http` 适合远程或容器部署。
- 使用结构化输出。
- 查询工具标记 `readOnlyHint=true`。
- backtest、benchmark、analyze 标记 `readOnlyHint=false`，因为可能保存记录、缓存数据或消耗 LLM 配额。
- 全部工具标记 `destructiveHint=false`，且没有券商执行工具。

### Standalone model runtime

- 使用标准 Chat Completions tool calling。
- provider preset 只提供默认 base URL、模型和 key 环境变量映射。
- `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 可覆盖 preset。
- 最大工具迭代次数防止无限循环。

## 薄适配器

### pi

pi adapter 负责注册 `quant_*` tool、把参数交给 CLI bridge，再把结构化结果返回给 harness。构建产物内联 bridge，不携带 workspace runtime dependency。

### dsh

dsh adapter 导出 Cordis `name`、`inject = ["tools"]` 与 `apply(ctx)`，并通过 `ctx.tools.register()` 注册 9 个 `quant_*` model tools。npm manifest 的 `dsh.bundle.patch` 指向 `cordis.patch.yml`，供当前 profile plugin CLI 安装。当前单元测试、RC 类型检查、Node smoke 和 bundle 构建已通过，但只有针对固定 dsh profile 完成加载、发现和真实调用 E2E 后，才能升级为 stable。

pi 与 dsh 都从 `@quant-trade/cli-bridge` 读取同一份 TypeScript schema snapshot、boolean flag serializer 和 tool timeout。dsh 不再维护第二份工具 schema。

## 关键数据流

### MCP 查询

```text
Harness model
  → tools/list
  ← 9 个 typed tools + annotations
  → tools/call quote
  → MCPServer
  → ToolRegistry.call("quote")
  → QuantTradeClient GET /api/quote
  ← backend JSON
  ← structuredContent
  ← harness model 解释结果
```

### pi/dsh 调用

```text
native adapter
  → buildCliArgs(params)
  → node:child_process spawn(uvx quant-trade-agent-tools <tool>)
  → Click CLI
  → ToolRegistry / QuantTradeClient
  ← JSON stdout
  → parseQuantOutput
  ← harness-native result
```

### 独立多模型 Agent

```text
agent-tools chat
  → resolve_provider
  → POST {base_url}/chat/completions + tool schemas
  ← tool_calls
  → ToolRegistry executes calls
  → append role=tool JSON
  → next completion
  ← final answer or iteration-limit error
```

## 部署模式

### 本机 stdio

Harness 启动 `uvx quant-trade-agent-tools mcp`。没有常驻 agent-tools daemon，进程生命周期由 harness 管理。

### 远程 MCP

以 `streamable-http` 启动 agent-tools，使用 `QUANT_TRADE_API_TOKEN` 连接受保护的上游。生产环境还应在 MCP 前放置 TLS、认证、请求限流和日志脱敏层。

### 原生 adapter

pi/dsh 在本机 spawn 已安装的 Python CLI。npm package 不携带 Python runtime，因此部署清单必须同时安装 `quant-trade-agent-tools`。

发布 bundle 不依赖全局 Bun；host 使用 Node.js >= 22.19 执行 adapter。Bun 仅属于源码 workspace 的依赖、测试与构建工具。dsh 的 `exec.signal` 会传递到 CLI bridge，取消时终止并等待子进程结束。

### 未来 harness

优先级：

1. harness 原生支持 MCP：只写配置，不建新 package。
2. harness 需要原生 UI/生命周期能力：写薄 adapter，调用 CLI 或 registry。
3. harness 使用不同模型：由 harness 自己管理模型；不改变工具实现。

## 与 `quant_trade` 的边界

允许：

- 调用稳定 HTTP API。
- 在 contract test 中使用 fake client/fake server。
- 文档记录上游 endpoint 与数据语义。

禁止：

- import `backend_llm`、Rust crate 或前端代码。
- 直接访问 PostgreSQL。
- 复制信号、指标、风控或 LangGraph 逻辑。
- 暴露下单、撤单或自动实盘工具。
- 持有 Git hosting、产品数据库或 broker 凭据。
- 创建或修改 Git hosting 对象、仓库工作树、订单、持仓或其他产品状态。

## 变更策略

- 工具新增/输入输出变更：先改 OpenSpec，再写 registry contract test，然后同步 MCP 与 adapter。
- 上游 endpoint 变更：只改 `QuantTradeClient` 和对应测试。
- 新模型：优先用 `custom`/环境覆盖；确有稳定价值时再增加 preset。
- 新 harness：优先 MCP；原生 adapter 必须独立测试和明确兼容版本。

新增 canonical tool 时必须同步：OpenSpec → Python client contract test → ToolRegistry → MCP test → TypeScript schema snapshot → pi/dsh test → README/功能文档。任何一步缺失都视为 schema drift。

## 故障隔离

| 故障 | 影响 | 隔离方式 |
|---|---|---|
| 上游 API 不可用 | 所有实时工具 | HTTP timeout、显式错误、harness 可重试 |
| 模型 endpoint 不可用 | 仅独立 `chat` | MCP/CLI 和 harness 自带模型不受影响 |
| pi API 变化 | 仅 pi package | adapter 单测与独立发布 |
| dsh API 变化 | 仅 experimental dsh package | 不影响 MCP、CLI、pi |
| schema 漂移 | 所有适配器 | canonical registry 测试 + 全工作区 CI |
| 上游 response shape 漂移 | 单个工具 | client normalization contract test |
| benchmark 长任务超时 | benchmark | Python/TS 统一 30 分钟 timeout |

## 信任与安全边界

- 模型输出不可信：tool name 和 JSON arguments 必须经过 registry/schema 校验。
- 上游响应不可信：HTTP 状态和 JSON shape 必须验证，不能把错误页面当数据。
- harness 不持有上游数据库凭据，只持有可撤销 API token。
- 模型 provider key 只用于独立 `chat`，MCP/pi/dsh 使用 harness 自带模型时无需暴露 provider key。
- 决策输出是建议；系统没有 order/cancel tool，无法从当前公共接口直接进入实盘执行。
