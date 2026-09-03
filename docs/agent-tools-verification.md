<!-- visibility: internal-only; sanitized -->

# 验证报告

## SDD/TDD 证据

- OpenSpec：`openspec/changes/standard-multi-harness-agent/`。
- 实施计划：`docs/plans/2026-09-01-standard-multi-harness-agent.md`。
- Harness 最佳实践 OpenSpec：`openspec/changes/official-harness-adapters/`。
- Harness 实施计划：`docs/plans/2026-09-01-official-harness-adapters.md`。
- Python 首轮测试因 `client`、`tools`、`providers`、`agent` 与真实 MCP 实现缺失而失败，随后最小实现转绿。
- provider key 与 MCP annotations 先新增失败契约测试，再实现并转绿。
- TypeScript spawn 测试先暴露临时 worktree 命令耦合，再改为仓库本地 `uv --project`。
- 上游 contract audit 先复现新闻 array、K 线 count、回测 request、benchmark filtering/timeout 五类失败，再在 `QuantTradeClient` 边界规范化。
- TypeScript 先复现 benchmark timeout export 缺失、strategy enum 漂移和过期 direct-import 描述，再让 pi/dsh 复用共享 schema/timeout。
- Gateway 首轮 contract tests 因 FastAPI extra 与 `agent_tools.gateway` 尚未实现而 collection 失败，随后按 health/capabilities → auth/error → context → legacy/chat 顺序转绿。
- Gateway provider 异常测试先复现未知异常泄露为纯文本 500、iteration limit 未规范化、429 被折叠为普通 502，再实现统一 error envelope 和专用 retryable code。
- orchestration mode 测试先复现 `native` 会被展示为 active 但仍执行 legacy 的静默错误，再改为启动时拒绝未实现模式。
- Harness 首轮红灯为 7 pass / 8 fail：明确复现 Bun runtime、取消未传播、dsh 无 `apply`/`tools` 注册、bundle patch 缺失和 wildcard peer；最小实现后相关契约 15/15 转绿。
- Release hardening 首轮为 1 pass / 4 fail：复现隐式 sdist、本机绝对路径、CI
  缺少 package gate 和 dsh 错用 stable tag；npm auth 测试随后先红后绿。
- 实际 sdist 解包发现 Hatch 会强制包含 `.gitignore`；按 Hatch standard builder
  的不可排除元数据规则修正规格，仍显式排除 monorepo、CI、OpenSpec 与本地计划。
- MCP 版本漂移测试先把运行时 package version 替换为 `9.9.9` 并复现 server
  仍报告 `0.2.0`，再改为复用 `agent_tools.__version__`。
- 首次远端 MR job 被 Runner 全局 PATH 选到 Python 3.15 alpha，MCP 测试因
  `rpds` native extension ABI 符号失败（73 pass / 1 fail）；新增 CI version
  contract 后以 `UV_PYTHON=3.14` 固定到已声明支持的版本线。
- Python 修复后的远端 job 已达到 74/74，随后因 shell Runner 未加载 mise Bun
  而在 `bun install` 失败；新增 PATH contract，并在 test/三个 publish job 显式
  加入 `$(mise where bun)/bin`。
- Contract v1 producer 首轮 focused test 在 collection 阶段因
  `agent_tools.gateway.intelligence` 不存在而失败（1 error）；随后实现 injectable
  application service、forced tool-call client、四个 endpoint 和严格 models，34/34 转绿。
- Producer OpenAPI snapshot 测试先因 `openapi/agent-gateway-v1.json` 不存在而 1 failed，
  加入 producer artifact 和 runtime compatibility test 后 3/3 转绿；refactor 后 Gateway
  focused suite 为 40/40。
- Native analyze 首轮 focused collection 因 `NativeAnalysisProvider` 和默认 provider
  selector 尚不存在而 2 errors；最小实现后只剩 `/v1/analyze` producer snapshot 缺失的
  1 failed，补齐 contract 后 native/settings/Gateway/OpenAPI focused suite 41/41 转绿。
- native failure/boundary tests 覆盖空/不完整 context 不调用模型、invalid structured output、
  timeout、429、provider config、`BUY/HOLD/SELL` 与 confidence `0/1` 边界，以及显式 legacy
  rollback；structured executor refactor 后四类 enrichment 与 chat 全套保持绿色。
- app-level legacy rollback 测试随后先复现严格 response model 因旧可选
  `question/news_summary` 字段返回 500，再用兼容 schema 与 `exclude_none` 修复；最终 focused
  suite 为 42/42。
- Wish producer 首轮 focused 为 17 passed / 34 failed：缺少 application method、route、
  capability 和 OpenAPI contract；最小实现后 50 passed / 1 failed，唯一红灯为 producer
  snapshot 缺失，补齐后 51/51 转绿。
- 空白 message/history 红测随后复现 2 failed / 7 passed；增加 wish-specific non-blank
  validation 和 requirement item bounds 后最终 focused 为 53/53。
- Real-provider smoke 首轮在 collection 阶段因 `agent_tools.staging_smoke` 不存在而 1 error；
  实现双门禁、injectable fake service、三项 contract check 和安全报告后 6 passed / 1 live
  skipped。safe-report unknown-field canary 随后先红，再改为显式 allowlist。
- Cross-repo verifier 追加门禁先复现 OpenAPI 4 passed / 3 failed：snapshot 缺 `/v1/chat`、
  `/v1/capabilities`，且旧成功响应 description 与 runtime 不完全一致；补齐严格 response
  models、GET/POST-aware exact parity 和 required-route test 后转绿，未删除任何 required route。
- Code-review producer focused 红灯为 36 failed / 30 passed：缺少两个 application method、
  route、capabilities 与 OpenAPI path；最小实现后 64 passed / 2 failed，唯一剩余红灯为 snapshot
  缺两个 path。由 runtime 生成 v1 snapshot 后 focused 66/66 转绿。
- Public documentation 首轮 focused 为 3 failed：README canonical terms、execution-doc marker 和
  publication scan 均按预期失败，scanner 仅报告 20 个 file/rule 类别。sdist canonical-doc
  allowlist 另有独立红灯；修正文档、metadata 与历史证据后 focused 10/10 转绿。
- Multi-symbol 首轮 Python focused 为 19 failed / 3 passed：缺少 symbol/interval forwarding、
  fail-closed validation、CLI/MCP schema，且测试检出本地策略默认参数复制。TypeScript 首轮为
  18 passed / 2 failed / 1 module error：缺共享 enum export 且 risk object 被序列化为
  `[object Object]`。最小实现及补充边界覆盖后 focused Python 48/48、TypeScript 29/29 转绿。
- Public review blocker 首轮 focused 5/5 失败：缺少专用 legacy client method、provider 错调
  canonical analyze、Gateway 丢弃已校验 symbol、runtime 未接收或绑定 selected symbol。最小修复后
  同组 5/5 转绿；相关 client/Gateway/runtime/tool 回归另检出一个使用旧 protocol 的测试替身，
  更新为 `legacy_analyze` 后转绿。
- Review blocker 完整门禁：Python 249 passed / 1 opt-in live case skipped，TypeScript 40 passed；
  Ruff、typecheck、pi/dsh build、Python sdist/wheel、strict OpenSpec、公开文档/发布 metadata、
  Bandit、pip-audit 与 bun audit 全部通过。

## 自动验证

```text
uv run pytest tests/ -q
74 passed

bun test packages/
32 passed, 0 failed, 115 expect() calls

bun run typecheck
passed

bun run build
pi dist/extension.js built
dsh dist/plugin.js built; cordis.patch.yml packaged

plain Node.js bundle smoke
pi registered/invoked 9 tools; dsh registered/invoked 9 tools

uv build
wheel and source distribution built for 0.2.0

uvx --from dist/*.whl agent-tools --version
agent-tools, version 0.2.0

isolated wheel listing + real Gateway process smoke
gateway modules packaged; /health and authenticated /v1/capabilities passed

npm pack --dry-run --json (pi + dsh package directories)
each tarball contains only README, package metadata, adapter artifact and required skill/manifest

actual archive extraction
sdist 31 files; wheel 20 files; pi 4 files; dsh 4 files
no developer home path, common credential pattern, or workspace runtime dependency

uvx isolated wheel smoke
CLI version/help/offline analyze passed
real Gateway process: health 200, unauthorized 401, authenticated capabilities 200 with 9 tools

plain Node.js bundle smoke
pi registered 9 tools; dsh injected tools service and registered 9 tools

uvx pip-audit
no known Python vulnerabilities

bun audit
no known vulnerabilities across 247 packages
```

最终发布构建与打包检查完成后，应在本报告追加最新结果。

### Contract v1 producer delivery evidence

```text
focused Gateway/application/OpenAPI: 40 passed
uv run pytest tests/ -q: 101 passed
bun test packages/: 32 passed, 0 failed
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
wheel inspection: intelligence.py + agent_tools/openapi/agent-gateway-v1.json present
git diff --check: passed
forbidden dependency/tool audit: no quant_trade import, DB access or order/cancel route/tool added
```

### Native analyze 第二解耦切片

```text
focused native/settings/Gateway/OpenAPI: 42 passed
uv run pytest tests/ -q: 125 passed
bun test packages/: 32 passed, 0 failed, 115 expect() calls
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
producer snapshot: /v1/analyze request/response exact runtime compatibility passed
wheel inspection: native Gateway modules + agent_tools/openapi/agent-gateway-v1.json present
git diff --check: passed
boundary audit: no quant_trade internal import, DB, order/cancel or broker mutation added
```

### Wish interpretation 第三解耦切片

```text
focused wish/Gateway/OpenAPI: 53 passed
uv run pytest tests/ -q: 158 passed
bun test packages/: 32 passed, 0 failed, 115 expect() calls
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
producer snapshot: /v1/interpret/wish request/response exact runtime compatibility passed
wheel inspection: wish runtime + agent_tools/openapi/agent-gateway-v1.json present
git diff --check: passed
boundary audit: no GitLab credential/client, issue mutation, product mutation API, DB,
                quant_trade internal import, order/cancel or broker capability added
```

### Opt-in real-provider smoke 与 snapshot parity

```text
focused smoke/OpenAPI/Gateway: 41 passed, 1 live skipped
RUN_REAL_PROVIDER_E2E=0 uv run pytest tests/ -q: 167 passed, 1 skipped
bun test packages/: 32 passed, 0 failed, 115 expect() calls
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
wheel inspection: staging_smoke.py + Gateway runtime + OpenAPI snapshot present
snapshot parity: all 8 required product routes, GET/POST exact runtime compatibility passed
git diff --check: passed
boundary audit: no GitLab credential/client, issue/product mutation, DB, internal import,
                order/cancel or broker capability added
```

Explicit live run after all gates:

| Provider/model | Contract check | Latency | Result |
|---|---|---:|---|
| configured provider / redacted model | translation | recorded outside repository | structured valid |
| configured provider / redacted model | wish clarifying | recorded outside repository | structured valid, `clarifying` |
| configured provider / redacted model | wish confirming | recorded outside repository | structured valid, `confirming` |

真实调用报告未包含 key、base URL、prompt/history、翻译/wish 正文、provider body 或异常原文。

### 跨仓产品真实 staging E2E

产品仓在隔离环境完成以下真实链路：HTTPS Gateway -> Rust consumer -> model provider ->
产品侧 mutation adapter。临时测试对象由产品 runner 与独立 API 均确认最终状态为 closed；
环境项目、对象和 endpoint 标识不保存在仓库中。

```text
cross-repo verifier: ok
Rust: 575 passed, 9 ignored
Python: 111 passed
frontend: 507 passed
frontend typecheck: passed
end-to-end status: passed
```

该证据不包含 token、URL、prompt 或模型正文。GitLab credential、issue mutation 和独立状态
复核均由产品侧执行，producer 边界未改变。

### Code review/respond producer

```text
focused service/Gateway/OpenAPI: 66 passed
RUN_REAL_PROVIDER_E2E=0 uv run pytest tests/ -q: 199 passed, 1 skipped
bun test packages/: 32 passed, 0 failed, 115 expect() calls
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
snapshot parity: all 10 required product routes, GET/POST exact runtime compatibility passed
wheel inspection: review runtime + agent_tools/openapi/agent-gateway-v1.json present
packaged snapshot: /v1/review/code and /v1/review/respond present, contract v1
git diff --check: passed
boundary audit: no sibling import, GitLab/DB/repository/coding-agent/trading mutation added
```

模型调用、prompt、forced structured schema 和 provider provenance 均由本仓
`GatewayIntelligenceService` 持有。产品只需传递严格有界文本并消费响应；两个 endpoint
无状态且不执行外部副作用。

### Public documentation hardening

```text
initial focused red: 3 failed; 20 redacted file/rule violations
sdist canonical-doc allowlist red: 1 failed
focused publication + release metadata: 10 passed
RUN_REAL_PROVIDER_E2E=0 uv run pytest tests/ -q: 202 passed, 1 skipped
bun test packages/: 32 passed, 0 failed, 115 expect() calls
bun run typecheck: passed
bun run build: pi/dsh bundles built
uv build: sdist + wheel built
artifact inspection: sdist 44 files; wheel 23 files; ARCHITECTURE/SECURITY present
npm pack dry-run: pi 4 files; dsh 4 files
git diff --check: passed
```

公开扫描覆盖 Markdown 与 release metadata，检查 canonical plane/security 术语、internal-only
sanitized marker、开发机路径、私有 network/remote、环境 ID、完整内部 revision、真实
provider/model assignment、credential value example 与 external URL allowlist。失败不会输出命中
值。本切片没有执行真实 provider 网络测试，也没有读取 sibling。

### Multi-symbol market/backtest tools

```text
focused Python: 48 passed
focused TypeScript: 29 passed, 0 failed, 135 assertions
exact request contract: quote/kline/signals/trending/historical/benchmark passed
real MCP: tools/list enum parity and 6981.T tools/call passed
local boundary: unknown symbol/interval rejected before network; no trading mutation tool
strategy boundary: string ID forwarded; no copied Rust defaults
producer contract: quant_trade!152 deployed in v1.5.62; optimizer hotfix v1.5.63 stable
RUN_REAL_PROVIDER_E2E=0 full Python: 230 passed, 1 skipped
Bun packages: 38 passed, 0 failed, 152 assertions
typecheck + pi/dsh build + uv build: passed
artifact: sdist 46 files, wheel 23 files; pi/dsh npm dry-runs 4 files each
publication/secret/boundary audit: passed; expected sdist test canaries remain test-only
branch pipeline + Draft MR !4 pipeline: passed; no conflicts; no merge/tag/deploy
```

News and aggregate sentiment deliberately remain global. Product source now contains backward-compatible
string-or-config parsing with Rust-only defaults, but production integration is not claimed green until
the bounded smoke passes and the product optimizer hotfix is deployed.

### Version 0.3.0 release preparation

```text
Python red: 2 failed, 6 passed (package metadata and capabilities still 0.2.0)
TypeScript red: 1 failed (root/bridge/pi/dsh manifests still 0.2.0)
focused Python green: 9 passed
focused TypeScript green: 1 passed
Python/uv + root/bridge/pi/dsh/Bun versions: 0.3.0
Gateway health/capabilities + MCP runtime version source: agent_tools.__version__
contract version: v1 unchanged
real product loopback smoke: v1.5.62 contract passed; v1.5.63 stability gate passed
RUN_REAL_PROVIDER_E2E=0 full Python: 230 passed, 1 skipped
Bun packages: 39 passed, 0 failed, 153 assertions
typecheck + pi/dsh build + uv build: passed
CLI + wheel metadata: 0.3.0
artifact: sdist 46 files, wheel 23 files; pi/dsh 0.3.0 npm dry-runs 4 files each
publication/secret/local-path/strategy-copy/internal-import audit: passed
```

### Version 0.3.1 source/artifact release governance

A previous tag passed repository tests but public registry uploads were rejected because the protected
credential/authorization prerequisites were not configured. That result is recorded as a tested source
revision with failed public publication, not as a published release. The hotfix makes the two states
independent and fail-closed.

```text
CI/lifecycle RED: 3 failed, 7 passed
CI/lifecycle focused GREEN: 10 passed
prepublishOnly dry-run: pi + dsh invoked Bash successfully; no upload performed
version RED: Python 1 failed, 9 passed; TypeScript 1 failed
version focused GREEN: Python release/capabilities 50 passed; TypeScript 1 passed
full Python: 233 passed, 1 opt-in live-provider test skipped
full Bun: 39 passed, 0 failed, 153 assertions
typecheck + pi/dsh build + uv build: passed
artifact audit: 2 Python release archives + 2 npm tarballs, all version 0.3.1
archive security: no credential/auth file, workstation path or workspace runtime dependency
public publication: not attempted; no tag, publish or deploy performed by this hotfix
```

The GitLab tag job is statically pinned to run after the full test gate and retain the same archive paths
used by the local package audit. PyPI and npm rules each require their explicit enable flag plus matching
credential and end with a disabled fallback. Absence of CI variables therefore skips public jobs without
weakening source artifact creation or claiming publication.

### Production loopback dual-symbol smoke

All calls used repository runtime `0.3.0`, loopback product HTTP, symbol `6981.T`, interval `15m`,
strategy string ID `rsi` and a five-day lookback. Reports retained only shape/latency/contract booleans;
they did not retain price, candles, trades, metrics, complete responses or environment coordinates.

```text
attempt 1: producer optimizer starvation; direct quote read timeout at 120s
short probes: 4 additional quote timeouts at 10s; no kline/backtest/MCP progression
attribution: producer runtime starvation, not adapter contract failure

attempt 2 after product restart:
  direct quote: 71ms, symbol/positive-price shape valid
  direct kline: 65ms, 8 candles
  direct historical: 574ms, string strategy ID accepted, response shape valid
  MCP quote: 1117ms, shape valid
  MCP kline: first timeout, second connection reset during producer starvation,
             third retry succeeded after operator restart; 8 candles
  MCP historical: 382ms, string strategy ID accepted, response shape valid
  script result: success after retry across restart

clean MCP-only retry in healthy window:
  quote: 1468ms, shape valid
  kline: 32ms, 8 candles
  historical: 629ms, string strategy ID accepted, response shape valid
  schema: symbol/interval enums and strategy type=string valid
  tool boundary: 9 tools, no order/cancel/broker/position mutation tool
  payload bodies recorded: false
  trading mutation attempted: false
```

Product `v1.5.63` deployed the optimizer isolation fix. Product-owned acceptance observed the optimizer
actively running, then repeatedly checked health and `6981.T` quote: every request returned HTTP 200,
quote identity remained correct and latency stayed in a bounded low-millisecond range. Exact optimizer
output, process metrics, host coordinates, commit/pipeline identifiers, prices and payload bodies are not
stored here. Together with the earlier client/MCP smoke, the readiness gate passed.

## 覆盖范围

| 层 | 覆盖 |
|---|---|
| HTTP client | 分离 API URL、Bearer auth、双标 query、新闻包装、K 线裁剪、字符串策略回测映射、benchmark 过滤/timeout、非法响应 |
| Tool registry | 9 个工具、schema、默认参数、禁止 order tools |
| Providers | 5 个 preset、厂商 key、通用覆盖、custom 校验 |
| Agent loop | tool call、结果回灌、最大迭代保护 |
| REST Gateway | optional import、health/capabilities、Bearer auth、request id、错误信封、history 限制 |
| ContextCollector | canonical registry、并行六源、RSI/Twitter 派生、partial failure、必需事实 gate |
| Gateway providers | legacy request/response 映射、benchmark policy、timeout/429/runtime error normalization |
| Native analysis | server facts、forced schema、layered contract、action/confidence 边界、provider failures、legacy rollback |
| Intelligence producer | 四个 v1 endpoint、forced structured output、score/ID 边界、一次 repair、provenance/warnings、OpenAPI compatibility |
| Wish interpretation | stateless history、phase-aware completeness、中文/enum/length boundaries、provider failures、consumer/OpenAPI compatibility |
| Staging smoke | default no-network gate、missing-key gate、translation/wish live contracts、latency、安全报告 allowlist |
| Cross-repo staging | 隔离 HTTPS Gateway、真实 Rust consumer、配置的 provider、产品侧 mutation/独立 closed 复核、verifier 与产品全量门禁 |
| Code review producer | diff/message/context bounds、untrusted-input prompt boundary、forced schema、verdict/文本边界、provider failures、route/OpenAPI parity、无副作用审计 |
| Public documentation | canonical architecture/security、README links、internal marker、redacted sensitive-value categories、URL allowlist、sdist inclusion |
| MCP | 9 个工具发现、结构化调用、查询/计算工具 annotations |
| CLI | 9 个命令、JSON 输出、离线 analyze |
| TS bridge | Node spawn、解析、schema、超时、harness cancellation 和错误 |
| pi | 官方 package/extension 注册、0.84.x peer、纯 Node 调用 |
| dsh | `apply`/`inject`、`ctx.tools.register`、bundle patch、RC types、取消传播 |
| Multi-symbol parity | client/registry/CLI/MCP/pi/dsh 的 symbol/interval enum、risk JSON、exact request 与 no-network failure |

## 安全检查

- 没有券商 order/cancel 工具。
- `.env.example` 只含空 key 示例。
- 凭据通过环境变量读取，不写入日志或配置产物。
- 适配器构建产物内联 bridge，不包含 workspace-only runtime dependency。
- 上游只通过 HTTP API 访问，不 import 内部代码、不直连数据库。
- Python sdist 使用显式 allowlist；wheel/sdist/npm 包均未发现本地绝对路径。
- npm CI auth 文件只包含 `${NPM_TOKEN}` 占位符，不包含 token 值。
- Wish producer 没有 GitLab token/client 或 issue/product mutation 调用；完整 issue payload 只在
  confirming/confirmed 作为 validated decision-support data 返回。
- staging runner 只有双 opt-in gate 后才构造 service；stdout allowlist 不含 key、base URL、
  prompt/history、模型输出或原始 provider error。
- code review/respond 不启动本地 coding agent、不读写仓库、不调用 GitLab/产品 mutation、DB
  或交易接口；diff/context/message 只作为不可信模型输入，输出必须通过 exact schema。
- 公开文档安全测试扫描全部 Markdown 与 release metadata，失败信息只显示文件和规则类别；
  canonical architecture/security 已进入 Python sdist。

## 尚未完成的外部验证

- 没有在目标 dsh 发布版本做真实 harness E2E，因此 dsh 保持 experimental。
- 已使用受控环境凭据完成一次 structured translation/wish staging smoke；其他 provider
  尚未进行真实联网验证，默认自动测试仍使用 fake transport 且 live case 默认 skipped。
- wish 路径已完成真实跨仓 staging E2E；行情在线数据路径仍未做对应真实 E2E，自动测试继续
  使用 fake client/fixture，避免 CI 依赖生产环境。
- 隔离 HTTPS staging 接入已经验证；正式生产路由、systemd 部署和 rollout monitoring 仍不在
  本次证据范围内。
- native analyze 已实现并成为默认模式；legacy 仅为显式回滚。shadow 尚未实现，会在启动时
  拒绝且不在 capabilities 中广告。
- wish interpretation producer/consumer 已完成；Twitter 已采用产品侧 raw connector + shared
  enrichment。durable enrichment worker/job 尚未实现。
- 远端仓库与项目专用 Runner 已配置；具体坐标保留在访问受控的运维配置中。
- 公共 registry publication 尚未验证；对应 enable flag、受保护 credential 与 registry
  authorization 未明确满足时，jobs 必须 skipped。source/artifact release 不再被这些条件阻塞。
- 推荐后续分别验证 PyPI/npm 的 OIDC/trusted-publishing 流程；在此之前只允许受保护 CI
  variables，不在仓库记录 credential 或 scope owner。
