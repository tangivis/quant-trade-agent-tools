# AGENTS.md — quant-trade-agent-tools 开发规范

## 强制流程

- 所有功能与行为变更必须执行 **SDD + TDD**。
- SDD 先写入 `openspec/changes/<change-name>/`；超过 3 个文件的变更另写 `docs/plans/` 实施计划。
- TDD 必须保留红-绿-重构证据：先写失败测试，再实现最小代码，最后运行相关全套验证。
- 每次修改必须更新 `CHANGELOG.md` 与受影响文档。
- 不得直接推送 `main`；使用 `feature/*` 分支并通过 MR 合并。

## Git Flow

- `main` 是默认且受保护的交付分支；任何角色都不得直接 push 或 force push。
- 新工作必须从最新 `origin/main` 创建 `feature/*` 分支，不得继续复用已经合入 main 的旧
  feature branch。
- 所有变更通过 MR 进入 `main`；pipeline 成功且全部 discussion resolved 后才允许合并。
- 项目使用 fast-forward merge，squash 默认开启，并在合并后自动删除远端 source branch。
- 搬迁含未提交工作的交付分支时，必须先确认两个 committed tree 一致，并完整保留 dirty
  tracked/untracked 内容；未经用户明确授权不得 stash、drop、reset 或 clean。

## 工具链

- Python 依赖、运行、测试与构建统一使用 `uv`。
- TypeScript 依赖、脚本、测试与构建统一使用 `bun`；仅 npm 发布命令使用 `npm publish`。
- Python 测试：`uv run pytest tests/ -v`。
- TypeScript 测试：`bun test packages/`。
- TypeScript 类型检查：`bun run typecheck`。
- 全部构建：`bun run build && uv build`。

## 架构边界

- 本仓库不得 import `quant_trade` 内部模块、访问其数据库或复制其业务实现。
- 与 `quant_trade` 的运行时集成只允许通过已发布 HTTP API。
- MCP/CLI 是稳定核心接口；pi、dsh 与未来 harness 必须保持薄适配器。
- 禁止增加券商下单、撤单或自动实盘执行工具。
- dsh 在完成对应版本端到端验证前必须标记为 experimental。

## Cross-Repo Contract v1

- `quant_trade` 拥有事实、确定性交易域逻辑、持久化、风控/执行边界和产品 UI。
- 本仓库拥有 LLM provider/key、prompt、tool calling、agent orchestration 与 harness adapter。
- 两仓库运行时只通过 producer 管理的版本化 HTTP API 集成；consumer 固定 contract
  snapshot 并运行 compatibility tests。
- Gateway REST 面向产品，MCP 面向 harness；一个仓库失败不得阻止另一个仓库核心能力启动。
- Agent 错误必须显式失败，不得伪装成成功 `HOLD`；provider key 不进入浏览器或 Data Plane。
- 跨仓库行为变更分别建立 OpenSpec、TDD、feature branch 和 MR，不创建跨仓库 commit。
- 恢复未完成任务时，先读本仓库 `docs/handoffs/CURRENT.md` 和 active OpenSpec。

## 安全

- 禁止提交 API key、token、cookie、密码、数据库连接串或 `.env`。
- 所有环境变量必须登记到 `.env.example`，示例值不得包含真实凭据。
- 发布前检查打包内容，不得包含 workspace-only 运行时依赖或本地绝对路径。
