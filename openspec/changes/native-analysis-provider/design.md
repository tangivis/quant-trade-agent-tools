# Design: Native Analysis Provider

## Runtime Flow

```text
quant_trade scheduler
       |
       | POST /v1/analyze {symbol, question, mode}
       v
ContextCollector
       | server-owned facts + derived values + source status
       v
NativeAnalysisProvider
       |
       | StructuredModelExecutor
       v
resolve_provider() + OpenAI-compatible forced function call
       |
       v
validated layered decision-support response
```

Native provider 不调用 `QuantTradeClient.analyze()`，所以不再依赖 legacy Python
`/agent/analyze`。它仍通过 ContextCollector/ToolRegistry 读取 `quant_trade` 的版本化 HTTP
事实 API，不 import 产品代码、不访问数据库。

## Shared Structured Model Boundary

上一切片的 provider resolution、HTTP/error mapping 和 forced tool-call transport 必须复用。
把它们收敛到可注入的 `StructuredModelExecutor`：

- `resolve_provider()` 生成 `ProviderConfig`；
- `StructuredOutputClient` 执行 OpenAI-compatible call；
- executor 统一映射 config、timeout、429、HTTP 和 invalid structured response；
- enrichment service 与 native analysis provider 共用 executor，但保留各自 prompt/schema 和
  domain normalization。

测试通过 fake structured client 注入 response 或异常，不使用真实 key。

## Context Gate

Native provider 要求：

- `facts` 非空；
- `current_price`、`regime`、`rsi`、`adx`、`news_sentiment` 均存在；
- `ContextCollector` 已完成 source freshness/warning 记录。

缺失时返回 `CONTEXT_INCOMPLETE` 503/retryable，不调用模型，也不补造默认数字。

## Structured Output

唯一 forced function 为 `record_native_analysis`，输出：

```json
{
  "summary": "趋势偏强，但波动率仍高",
  "trend_direction": "UP",
  "action": "HOLD",
  "confidence": 0.72,
  "approved": false,
  "risk_notes": ["波动率较高"]
}
```

约束：

- exact keys；
- `summary` 为非空有界字符串；
- `trend_direction` 为 `UP|DOWN|SIDEWAYS|UNCLEAR`；
- `action` 为 `BUY|HOLD|SELL`；
- `confidence` 是有限 `[0,1]`，越界不 clamp，直接失败；
- `approved` 必须是真正 boolean；
- risk notes 是有界非空字符串数组。

模型只生成 interpretation/decision。响应中的 `facts`、`as_of`、context tools 和 upstream
warnings 来自 server，不信任模型。

## Layered Response

```text
facts       = snapshot.facts
analysis    = summary + trend_direction
decision    = action + confidence + approved + risk_notes
provenance  = provider + model + successful context source names
warnings    = snapshot warnings + decision_support_only
```

该 shape 与 `quant_trade::agent_gateway::AnalyzeResponse` fixture 兼容。`approved` 仅是风险
分析字段，不授权或触发交易。

## Mode Selection

- 默认：`native`。
- 显式 `legacy`：构造 `LegacyAnalysisProvider` 作为 rollback。
- `shadow`：本 change 不实现，配置时启动失败。

Capabilities：

```json
{
  "orchestration_modes": {
    "active": "native",
    "available": ["native", "legacy"],
    "planned": []
  }
}
```

不能把未实现的 shadow 广告为 available 或 planned。
