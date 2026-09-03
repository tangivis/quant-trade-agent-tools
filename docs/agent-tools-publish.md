# 发布与接入

本页是发布操作补充；正式职责与安全边界以仓库根目录 `ARCHITECTURE.md` 和 `SECURITY.md`
为准。公开文档不记录生产地址、账户、凭据值或实际 provider/model 选择。

## 发布物

| 发布物 | 用途 | 稳定性 |
|---|---|---|
| `quant-trade-agent-tools` | CLI、MCP、独立 model runtime | Beta |
| `@quant-trade/agent-tools-pi` | pi 原生 extension | Beta |
| `@quant-trade/agent-tools-dsh` | DeepSeek Harness/Cordis adapter | Experimental |

## 发布前门禁

所有发布必须经过 SDD + TDD，并运行：

```bash
uv sync --extra dev
uv run pytest tests/ -v
bun install --frozen-lockfile
bun test packages/
bun run typecheck
bun run build
uv build
```

还必须检查：

- `git diff --staged` 不含 key、token、cookie、`.env` 或绝对开发路径。
- Python wheel/sdist 和 npm tarball 只包含预期文件。
- npm 产物不含 `workspace:*` runtime dependency。
- dsh 若未完成目标版本 E2E，不得宣称 stable。
- tag pipeline 无论是否配置 registry credential，都必须保留 Python sdist/wheel 与 pi/dsh
  npm tarball；保留制品成功只代表 source/artifact release。
- 公共 PyPI publication 只有 `ENABLE_PYPI_PUBLISH=true` 与受保护 `PYPI_TOKEN` 同时存在时
  才运行；公共 npm publication 同理要求 `ENABLE_NPM_PUBLISH=true` 与受保护 `NPM_TOKEN`。
- npm publish job 通过 `.npmrc.ci` 的环境变量占位符消费 token，仓库与 artifact 都不保存
  credential 值。缺少任一 enable/credential 条件时 job 必须 skipped，不能报告 published。

## 两类独立发布状态

| 状态 | 成功条件 | 是否需要 registry credential | 可声明内容 |
|---|---|---|---|
| Source/artifact release | tag 的全量 test 与 artifact job 成功，GitLab 保留四类 archive | 否 | tag 与可下载 artifact 已就绪 |
| Public registry publication | 对应 opt-in job 成功上传已保留 artifact | 是，或未来受信发布身份 | 仅声明已成功的具体 registry/package |

一个 registry 的成功或失败不改变另一个 registry 的状态，也不改变已保留 artifact 的状态。
tag pipeline 中的 `source-release-artifacts` job 会保留：

- `dist/*.tar.gz` 与 `dist/*.whl`；
- `release-artifacts/npm/quant-trade-agent-tools-pi-*.tgz`；
- `release-artifacts/npm/quant-trade-agent-tools-dsh-*.tgz`。

公共 publication job 只消费这些 archive，不重新构建。长期推荐使用 registry 支持的
OIDC/trusted publishing，以短期工作负载身份取代长期 token；在该流程完成 SDD/TDD 与实际
验证前，masked + protected CI variables 是唯一允许的 token fallback。仓库文档不记录真实
credential、scope owner 或账户信息。

## PyPI/uv 安装

发布后可直接启动 MCP：

```bash
uvx quant-trade-agent-tools mcp
```

也可安装到持久环境：

```bash
uv tool install quant-trade-agent-tools
agent-tools quote
```

## MCP 接入

stdio client 的最小配置：

```json
{
  "mcpServers": {
    "quant-trade": {
      "command": "uvx",
      "args": ["quant-trade-agent-tools", "mcp"],
      "env": {
        "QUANT_TRADE_API_URL": "http://127.0.0.1:5188",
        "QUANT_TRADE_GATEWAY_URL": "http://127.0.0.1:8010"
      }
    }
  }
}
```

MCP harness 使用自己的 GPT、Claude、DeepSeek、Kimi 或其他模型；agent-tools 不限制模型供应商。

## pi

```bash
pi install npm:@quant-trade/agent-tools-pi
```

pi adapter 注册 12 个 `quant_*` tools，通过 `uvx quant-trade-agent-tools` 调用稳定 CLI。发布前需要在干净环境完成一次安装、工具发现和真实 API 调用。

当前验证并声明的 peer API 为 `@earendil-works/pi-coding-agent` 0.84.x。adapter bundle 使用 Node.js `child_process`，因此 host 运行时不再隐式依赖 Bun；开发测试和构建仍按仓库规范使用 Bun。

## dsh

`@quant-trade/agent-tools-dsh` 当前只发布 experimental tag。package 已声明 `dsh.bundle.patch`，可按当前 profile CLI 安装：

```bash
dsh plugin --profile <profile> add @quant-trade/agent-tools-dsh@experimental
```

插件通过 Cordis `apply`/`inject` 生命周期和 `ctx.tools.register()` 注册模型工具。当前类型检查固定在 Cordis 4.0.x 与 `@deepseek-ai/dsh-tools` 0.1.1-rc.2；该 RC contract 不能视为未来稳定协议。

稳定发布的额外门禁：

1. 固定 dsh 与 Cordis 版本。
2. 在干净环境安装 npm package。
3. 验证 plugin 被加载。
4. 验证 12 个工具可发现。
5. 至少真实调用 `quote` 和带参数的 `kline`。
6. 记录兼容矩阵和回退方案。

## Native adapter 运行依赖

pi 与 dsh 的发布 bundle 都内联内部 CLI bridge，不包含 `workspace:*` runtime dependency，也不引用相邻 `../quant_trade` 仓库。运行环境必须提供：

- Node.js >= 22.19；
- `uv`/`uvx`，且 `uvx quant-trade-agent-tools` 可执行；
- 可达的产品 HTTP API 与 Intelligence Gateway，通过 `QUANT_TRADE_API_URL`、
  `QUANT_TRADE_GATEWAY_URL`、`QUANT_TRADE_API_TOKEN` 和 `QUANT_TRADE_AGENT_TOKEN` 分别配置。

Bun 只用于本仓库 TypeScript 安装、测试和构建。

## 多模型模式

独立 `chat` 使用 OpenAI-compatible endpoint。provider、model、endpoint 与凭据由部署者在
受控运行配置和 secret store 中提供，不能进入公开文档或浏览器。供应商 API 变化时，环境
覆盖优先于代码 preset；可用字段见 `.env.example`，命令参数见 `agent-tools chat --help`。

## 版本策略

- Python、根 workspace、pi、dsh 和内部 bridge 同步版本。
- tool contract 的 breaking change 提升 major。
- 新 provider preset、新 transport 或兼容 adapter 提升 minor。
- 文档、错误处理和兼容修复提升 patch。
- Git tag `vX.Y.Z` 必定触发 source/artifact build；公共 publish jobs 只在各自 opt-in 条件满足
  时运行。tag 或 artifact success 本身不是 published 证明。

## 远端发布顺序

1. 在 `feature/*` 分支完成 SDD/TDD 与本页全部门禁，通过 MR 合并到受保护的
   `main`，不得直接 push `main`。
2. 确认 Python、根 workspace、pi、dsh、bridge 版本一致，且 release tag 必须
   精确等于 `v$(uv version --short)`。
3. 保护 `v*` tag；从已合并且门禁通过的 `main` commit 创建 `vX.Y.Z` tag。即使不配置任何
   registry credential，该 pipeline 也必须产出并保留 source artifacts。
4. 如需公共 PyPI publication，在 protected CI context 同时设置 Python enable flag 与
   credential；如需 npm publication，同理设置 npm enable flag 与 credential。未满足时保持
   skipped，不重试无凭据上传。
5. 分别核对 artifact release、PyPI 与 npm 的实际 job 状态；只声明确实成功的状态。Python
   与 pi 使用 stable channel；dsh 在固定 host E2E 完成前只使用 `experimental` dist-tag。

当前 npm package 使用公共 scope `@quant-trade`。首次发布前，token 所属 npm
账户必须拥有该 scope 的 publish 权限；包名未被发布不等于当前账户自动拥有 scope。
