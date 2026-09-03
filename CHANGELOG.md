# Changelog

## [Unreleased]

### Fixed

- Keep explicit legacy analysis rollback on the product-owned `/agent/analyze` endpoint through a
  separately named client method; it no longer calls the native, keyword-only Gateway analyze client or
  risks recursive dispatch.
- Bind the validated Gateway chat symbol into user-role model context and use it only as the default for
  symbol-scoped tool calls that omit `symbol`. Explicit tool symbols remain authoritative, while global
  news and sentiment calls remain unscoped.

### Security

- Keep caller-owned conversation summaries in a JSON-encoded user-role message; only the fixed repository
  policy is sent with system authority.
- Exclude all product-owned conversation tools from the Gateway's internal chat agent so untrusted model
  output cannot use a server credential to read or mutate conversation records.

### Added

- Public `0.4.0` release activation metadata for the registered PyPI Trusted Publisher, with exact Pages,
  README and publication-guide status while npm packages and dsh stability remain explicitly unclaimed.

- Credential-free public GitHub pull-request CI with immutable, Node 24-native action revisions, read-only
  repository permission, locked installs, Python/TypeScript verification, builds and package inspection.
- Executable workflow metadata test proving the public CI does not reference provider/PyPI/npm credentials
  or enable the opt-in real-provider smoke path.
- Public protected-main delivery now requires the successful, strict `verify` check in addition to review
  and resolved conversations; the validated workflow itself remains credential-free.
- Curated, script-free GitHub Pages content and a pinned Pages workflow that publishes only `site/`, never
  mixed-visibility execution documents.
- A tag-only GitHub release workflow that runs full gates, retains Python and pi/dsh archives, attaches the
  same files plus SHA-256 checksums to a GitHub Release, and keeps PyPI publication independently opt-in.
- Tokenless PyPI Trusted Publishing through a dedicated `pypi` environment and repository enable variable;
  no PyPI password or API token is accepted by the public workflow.
- Public repository delivery metadata now exposes the future Pages homepage while the OIDC publication
  switch remains disabled until external PyPI trust registration is complete.
- Release tags are protected against update/deletion and fail closed unless their commit is reachable from
  protected `main` and their name exactly matches the synchronized package version.

- Product-owned conversation integration: canonical `conversation_create`, `conversation_context` and
  `conversation_append` tools across Python CLI, MCP, pi and dsh adapters without database access.
- Stateless `POST /v1/summarize/conversation` producer and optional `context_summary` input for chat,
  with bounded schemas, structured output, OpenAPI snapshot and compatibility tests.
- Conversation-context OpenSpec, TDD plan and public architecture boundary documentation.
- Dual-symbol Gateway chat/analyze contracts for `9984.T|6981.T`; context collection now forwards the
  requested symbol to quote, kline, signals and trending tools.
- Full verification passed: Python `246 passed / 1 skipped`, TypeScript `40 passed`, Ruff, typecheck,
  pi/dsh bundles, Python sdist/wheel, isolated wheel execution, npm dry-runs and dependency/security audits;
  the product cross-repository verifier accepted all boundaries.

- Source/artifact release governance specification and implementation plan: tag-retained archives are
  defined independently from optional public PyPI/npm publication, without recording registry secrets
  or ownership details.
- Public release-state documentation, sanitized verification/handoff evidence and an MR delivery draft
  covering opt-in publication, OIDC/trusted-publishing follow-up and immutable-state rollback semantics.
- Delivery metadata records the Ready protected-main MR and successful head-pipeline gate without
  authorizing merge, tag, public publication or deployment.
- Sanitized production loopback evidence for `0.3.0`: direct client and real MCP validated `6981.T`
  quote, 15m kline and five-day RSI historical backtest with a string strategy ID; no market/backtest
  payload bodies or trading mutation calls were recorded.
- Dual-symbol canonical contracts for `quote`, `kline`, `signals`, `trending`, `backtest` and
  `benchmark`: only `9984.T|6981.T` and `1m|5m|15m|1h|1d|1wk` are accepted, with local fail-closed
  validation across client, registry, CLI, real MCP and pi/dsh shared schema snapshots.
- Exact historical/benchmark HTTP mapping for symbol, interval, optional initial cash and risk object;
  structured TypeScript arguments are serialized as JSON and benchmark retains the expensive-tool
  timeout/policy.
- Multi-symbol OpenSpec, implementation plan, request/parity/mutation-boundary tests and producer-first
  release evidence. News and sentiment remain explicitly global rather than pretending symbol isolation.
- 根目录 `ARCHITECTURE.md` 与 `SECURITY.md`，作为公开的双平面职责、层级关系、调用边界、
  trust boundary、credential、privacy、logging 与 vulnerability reporting 规范。
- 可执行的公开文档安全测试：要求 README/architecture/security canonical sections 与内部执行
  文档 visibility marker，并按文件/规则脱敏报告开发机路径、私有网络/remote、环境 ID、真实
  provider/model 配置和凭据值示例。
- 跨仓真实 staging 验收证据：隔离 HTTPS Gateway 经真实 Rust consumer、配置的模型 provider
  到产品侧 mutation adapter；临时测试对象由 runner 与独立 API 确认 closed，cross-repo
  verifier 与产品 Rust/Python/frontend 全量门禁通过，环境标识不进入仓库。
- `docs/mr/2026-09-01-contract-v1-intelligence-producers.md` 独立 MR draft，记录 producer-first
  dependency、contract/security、脱敏真实 provider 证据、rollout/rollback 与已知限制。
- Opt-in real-provider staging smoke：只有 `RUN_REAL_PROVIDER_E2E=1` 且 provider key 存在时
  才真实调用 translation、wish clarifying 和 wish confirming；默认测试绝不联网。
- staging safe-report allowlist，仅输出 provider/model、contract、latency、phase 和结构校验，
  丢弃 key、base URL、prompt、history、模型正文和原始异常 message。
- 默认 skip 的 live pytest case，以及 gate、missing-key、三任务 mock、错误脱敏和无 mutation
  source audit tests。
- `POST /v1/review/code`：接收有界 diff 与可选 project context，通过 provider-neutral forced
  structured output 返回 review、`LGTM|NEEDS_CHANGES`、provenance 和 warnings。
- `POST /v1/review/respond`：接收有界 message/context，返回无状态、无副作用的 structured
  reply；所有模型调用与 prompt 仅存在于 agent-tools。
- code review producer OpenSpec、实施计划、严格 route/service/OpenAPI contract tests，以及
  GitLab/DB/仓库/coding-agent/交易 mutation 边界审计。
- `POST /v1/interpret/wish`：无状态解释 `message + history`，输出
  clarifying/confirming/confirmed phase-aware wish contract；confirming/confirmed 必须重复完整、
  严格验证的 title/type/priority/requirements/summary。
- wish interpretation 使用共享 provider-neutral forced structured executor，并覆盖恶意枚举、
  额外字段、空/超长内容、history 重建、timeout、429 和 provider failure。
- wish producer request/response OpenAPI snapshot 与 `quant_trade` consumer fixture compatibility
  tests；GitLab token 与 issue mutation 继续只属于产品仓库。
- `NativeAnalysisProvider`：从 `ContextCollector` 的 server-owned facts 生成严格的
  `facts/analysis/decision/provenance/warnings` layered response，不再调用 legacy Python
  `/agent/analyze`。
- native analyze forced structured tool/schema、action/trend/confidence/approved/risk-notes
  边界校验，以及 provider config、timeout、429 和非法响应的统一 `GatewayError` 映射。
- `/v1/analyze` producer OpenAPI request/response schemas 与 `quant_trade` consumer fixture
  compatibility tests。
- Contract v1 Intelligence Plane producer endpoints：标题批量情感、聚合情感、跳空叙事和翻译。
- Provider-neutral `GatewayIntelligenceService` 与 OpenAI-compatible forced tool-call client；支持 fake client/service 注入测试。
- headline score 有限值 clamp、请求 ID 子集/重复检查、一次 missing-ID repair 和显式 residual missing warning。
- `openapi/agent-gateway-v1.json` producer snapshot 及 runtime compatibility tests。
- `Cross-Repo Contract v1`、producer OpenSpec、实施计划和跨 session handoff。

### Changed

- Prepare `0.4.0` across Python, root workspace, CLI bridge, pi and dsh packages because the pre-1.0
  canonical analyze input contract is intentionally corrected rather than reusing immutable `0.3.1`.
- Canonical `analyze` now accepts only `symbol` and optional `question`, calls native `POST /v1/analyze`,
  and lets the Gateway collect authoritative product facts. Product and Gateway Bearer credentials are
  configured independently.
- Pi now forwards host cancellation to the shared CLI subprocess, matching dsh behavior.
- Public package metadata points to the public GitHub source repository and describes all 12 current tools.
- CI runs the repository Ruff error/import/modern-typing rules in addition to Python tests.

- Release metadata is synchronized at `0.3.1` across Python runtime/build metadata, capabilities, the
  root/bridge/pi/dsh packages and workspace locks for the source-artifact governance hotfix.
- Tag pipelines now separate credential-independent source/artifact retention from optional public
  registry publication. PyPI and npm jobs consume the retained archives only when their registry-specific
  enable flag and credential are both present; disabled jobs do not claim publication.
- Release metadata is synchronized at `0.3.0` across Python runtime/build metadata, root/bridge/pi/dsh
  TypeScript packages and workspace locks; health, capabilities, CLI and MCP all derive the same runtime
  version while the API contract remains `v1`.
- Historical backtest now forwards the caller's string strategy ID without local strategy defaults or
  Rust config reconstruction. Product MR `quant_trade!152` has landed the compatible producer on product
  `main` and product `v1.5.62` passed the bounded contract smoke. Two observed timeout/reset windows were
  traced to producer optimizer starvation. Product `v1.5.63` deployed the hotfix and passed repeated
  health/second-symbol quote checks while the optimizer was active; default resolution/unknown-ID
  rejection stays solely in Rust.
- README、详细架构、发布与迁移文档统一采用 Intelligence Plane 与 Product/Data/Domain Plane
  定位；明确本仓没有产品 DB、Git hosting、repository 或 order/broker mutation。
- 历史 handoff/MR/verification/extraction 文档标记为 internal-only sanitized，并删除私有远端、
  工作站路径、环境 project/object、实际 provider/model 与 latency 细节；公开 package metadata
  不再包含私有 repository coordinate。
- Python sdist allowlist 增加公开 `ARCHITECTURE.md` 与 `SECURITY.md`。
- Git Flow 固定为从最新 `origin/main` 创建一次性交付 `feature/*` 分支，通过受保护 main 的
  fast-forward MR 合并；默认 squash，要求 pipeline 成功及全部 discussion resolved，并在
  合并后删除远端 source branch。交付内容已完整迁移至
  `feature/agent-decoupling-delivery`，未使用 stash/drop。
- producer OpenAPI snapshot 补齐已存在的 `POST /v1/chat` 与 `GET /v1/capabilities`；local
  verifier 现在支持 GET/POST exact runtime parity，required product routes 不降级。
- chat/capabilities 增加严格 response models，使跨仓库 consumer 可固定稳定 schema。
- `/v1/capabilities.intelligence_tasks` 在 producer 完成后增加 `wish_interpretation`。
- Gateway orchestration 默认从 `legacy` 切为 `native`；`legacy` 保留为显式回滚，未实现的
  `shadow` 继续拒绝启动且不在 capabilities 中虚假广告。
- `/v1/capabilities.orchestration_modes` 现在报告 active `native`、available
  `native/legacy`、planned 空列表。
- enrichment 与 native analyze 共用 provider-neutral `StructuredModelExecutor`，不复制
  provider 解析和模型错误规范化。
- `/v1/capabilities.intelligence_tasks` 只广告已实现的 analysis、chat 与四类 enrichment 能力。
- 四类 intelligence response 统一返回 v1 contract、request ID、provider/model provenance 和 warnings，并复用现有 Gateway error envelope。
- Python sdist 显式包含 producer OpenAPI contract。

## [0.2.0] - 2026-09-01

### Added

- 独立的 `QuantTradeClient` 与 9 个 canonical tool registry，通过公开 HTTP API 连接 `quant_trade`。
- 基于官方 MCP Python SDK v2 的 stdio 与 Streamable HTTP server。
- OpenAI-compatible 独立 agent runtime，支持 GPT、DeepSeek、Kimi、MiniMax、Ollama 与自定义 endpoint。
- 仓库级 SDD + TDD 规范、OpenSpec 变更、实施计划与环境变量示例。
- Python client、tool、provider、agent loop、MCP 契约测试。
- `docs/detailed-functions.md`：逐项记录 9 个工具的输入、默认值、上游 endpoint、输出、副作用和调用示例。
- `docs/architecture/quant-trade-agent-gateway-integration.md` 与对应 OpenSpec：设计 REST Agent Gateway + MCP 双接口、nginx 同源路由、legacy/native/shadow 分阶段迁移方案。
- `docs/plans/2026-09-01-agent-gateway-integration.md`：定义 Gateway、认证、ContextCollector、产品接入、shadow 和 legacy 退役的 TDD 实施顺序。
- 可选 FastAPI REST Agent Gateway：提供 `/health`、`/v1/capabilities`、`/v1/analyze`、`/v1/chat` 与延迟加载 CLI 启动命令。
- Gateway TDD 契约：覆盖 Bearer 鉴权、request id、错误信封、服务端行情上下文、partial failure、legacy 映射、无状态 history 和高成本工具政策。
- dsh npm bundle manifest 与 `cordis.patch.yml`，可由当前 `dsh plugin` profile 机制识别并插入插件。

### Changed

- 从临时目录迁移为可独立 clone、版本化和发布的 Git 仓库。
- 收紧 Python sdist 发布边界，移除发布文档中的开发机绝对路径，并把构建与包检查纳入 tag 发布前 CI 门禁。
- dsh 在完成固定版本真实 E2E 前仅使用 npm `experimental` dist-tag。
- MCP server 的版本字段改为复用 Python package `__version__`，避免发布版本漂移。
- GitLab CI 显式固定 Python 3.14，避免 Runner 全局 PATH 选择未支持的预发布解释器。
- GitLab test/publish jobs 显式加入 mise 管理的 Bun 路径，不依赖交互 shell 配置。
- pi/dsh 适配器内联共享 bridge，发布包不再依赖 workspace-only runtime package。
- 根 TypeScript project references、Bun 构建命令与 CI 验证改为全工作区检查。
- dsh 明确标记为 experimental，等待目标版本真实 harness 端到端验证。
- 按厂商当前官方文档更新 DeepSeek V4 Flash 与 Kimi K3 preset，并兼容 Kimi 的旧环境变量别名。
- 配置正式 GitLab remote，并为 Python、根 workspace、pi、dsh package 增加 repository metadata。
- `OpenAICompatibleAgent` 支持调用方有界 history、已调用工具追踪和显式资源关闭；REST 与 MCP 复用 canonical `ToolRegistry`。
- 未实现的 native/shadow 模式改为启动时明确拒绝，避免 capabilities 与实际 legacy 行为不一致；模型/legacy 上游 429 使用可重试专用错误码。
- dsh 从自定义 `ctx["quant.*"]` consumer shim 改为官方 Cordis `apply`/`inject` 生命周期，并通过 `ctx.tools.register()` 注册 9 个 `quant_*` 工具。
- pi host peer 收窄到已验证的 `0.84.x` API；dsh 类型契约固定为 Cordis `4.0.x` 与 `dsh-tools 0.1.1-rc.2`，但仍保持 experimental。
- 共享 CLI bridge 从 `Bun.spawn` 改为 `node:child_process`，Bun 只用于源码测试与构建，发布 adapter 可在 host 支持的 Node.js 运行时执行。

### Fixed

- pi/dsh npm lifecycle builds now execute shell scripts through Bash, preventing Bun from interpreting
  shell builtins during `prepublishOnly`.
- `analyze` 请求错误发送到行情 API 端口的问题。
- Python module 入口的错误绝对导入。
- 本地 TypeScript spawn 测试依赖临时 worktree 路径的问题。
- pi/dsh 把 Click boolean flag 错误序列化为 `--flag true` 的问题。
- 新闻数组响应、K 线 `count`、历史回测 `StrategyConfig`、benchmark 过滤和 30 分钟 timeout 与上游 API 不一致的问题。
- dsh 内重复维护第二份工具 schema 导致的跨 harness 漂移风险。
- pi/dsh 发布包隐式要求全局 Bun、无法在普通 Node host 中执行的问题。
- dsh 未通过 `tools` service 注册模型工具、旧 `cordis.yml` 也不能作为当前 `dsh.bundle` 安装层的问题。

## [0.1.0] - 2026-08-31

### Added

- 初始 Python CLI、pi extension、dsh Cordis adapter 与共享 TypeScript bridge。
