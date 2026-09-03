# Design: Contract v1 Intelligence Producer

## Boundary

```text
quant_trade consumer
       |
       | versioned REST JSON
       v
Gateway route + Pydantic contract
       |
       v
GatewayIntelligenceService
       |
       +-- resolve_provider() -> ProviderConfig
       |
       +-- StructuredOutputClient protocol
               |
               v
       OpenAI-compatible /chat/completions
       forced function/tool call
```

路由不包含 prompt、provider HTTP 或 output repair 逻辑。application service 可被 REST、
未来 MCP 或 worker 共用；测试通过注入 fake service/fake structured client，不发真实网络请求。

## Input Contracts

所有输入 model 使用 `extra="forbid"`：

- headline item ID 为整数且单个 request 内唯一；标题非空。
- headline batch、summary headlines 和 gap headlines 都设置有界数量与文本长度。
- 当前 symbol 固定为 `9984.T`，translation target 固定为 `zh-CN`。
- 非法/额外字段继续进入现有 `VALIDATION_ERROR` envelope。

## Structured Completion

默认 client 调 OpenAI-compatible `POST {base_url}/chat/completions`：

- server-side Bearer key；
- `tools` 中只有本任务的单个 function schema；
- `tool_choice` 强制该 function；
- 只解析对应 function 的 JSON arguments；
- 不把 provider response body、base URL 或 raw reasoning 返回调用方。

Application service 对解析结果执行第二层校验。HTTP/provider 异常统一映射为 Gateway
已有 `PROVIDER_CONFIG_ERROR`、`MODEL_TIMEOUT`、`MODEL_RATE_LIMIT`、`MODEL_ERROR` 或
`MODEL_RESPONSE_ERROR`。

## Headline Sentiment Repair

1. 首次请求包含全部 `{id,title,language}`。
2. 验证 output `scores` 是 list，ID 是请求 ID 的唯一子集，score 是有限数。
3. score clamp 到 `[-1,1]`。
4. 计算 missing IDs；若非空，只以 missing items 发起一次 repair。
5. repair output 仍执行相同 ID/score 校验，并与第一次结果合并。
6. 最终按原请求顺序返回 scores；仍缺失的 ID 放入 `missing_ids`，并增加
   `missing_ids_after_repair` warning。

未知 ID 或重复 ID 是 provider contract violation，不能静默忽略；它们映射为
`MODEL_RESPONSE_ERROR`。

## Other Task Normalization

- summary：score clamp；label/sub-sentiment/alignment 使用枚举；`article_count` 和
  `analyzed_at` 由 service 生成，不信任模型。
- gap：只接受非空、最多 60 字的简体中文叙事，并拒绝明显目标价、止损、买卖建议或
  后市预测短语。
- translation：只接受非空 translated string。

## Common Success Metadata

路由在 application result 外包裹：

```json
{
  "request_id": "...",
  "contract_version": "v1",
  "provenance": {"provider": "...", "model": "..."},
  "warnings": []
}
```

`X-Request-ID` 继续由既有 middleware 接收或生成并回显。

## Capability Honesty

`intelligence_tasks` 由代码常量维护，只包含已注册且通过测试的：

- `headline_sentiment`
- `bundled_sentiment`
- `gap_narrative`
- `translation`
- `chat`
- `analysis`

未来 task 必须先实现和测试，再加入该列表。
