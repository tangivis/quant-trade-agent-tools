---
name: agent-tools
description: 9984.T 与 6981.T 量化交易工具集. 当用户问及两个受支持标的的行情、信号、回测或多 agent 交易决策时使用.
---

# agent-tools — quant_trade 量化交易工具

quant_trade 后端的 12 个能力，以 MCP tool 形式暴露。行情与回测工具支持 **9984.T** 和
**6981.T**；新闻与聚合情感是全局源，不按 symbol 隔离。

## When to use

- 用户问 9984.T 或 6981.T 的**当前价格/行情/今日走势** → `quant_quote`
- 用户问 9984.T 或 6981.T 的 **K线/历史数据/图表** → `quant_kline`
- 用户问"现在有什么信号"/"技术面怎么看" → `quant_signals`
- 用户问**全局最近新闻** → `quant_news`（不要描述为已按 symbol 过滤）
- 用户问"新闻面情绪如何" → `quant_sentiment`
- 用户问**趋势/regime/ADX/RSI** → `quant_trending`
- 用户要求**回测某个策略** → `quant_backtest` (需 strategy 名字)
- 用户要求**扫描参数空间找最优参数** → `quant_benchmark`
- 用户要求 **LLM 综合分析/多 agent 交易决策** → `quant_analyze`
- 用户需要跨 harness 创建、读取或追加产品会话 → `quant_conversation_create`、`quant_conversation_context`、`quant_conversation_append`

## Inputs

六个 symbol-scoped 工具只接受 `9984.T|6981.T`；其它参数按需：
- `quant_quote`, `quant_signals`, `quant_trending`: `symbol`
- `quant_kline`: `symbol`, `interval` (1m/5m/15m/1h/1d/1wk), `count` (int)
- `quant_news`: `count` (int, default 10)
- `quant_sentiment`: 无 symbol；全局聚合
- `quant_backtest`: `symbol`, `strategy`, `interval`, `days`, 可选 `initial_cash`, `risk_params`
- `quant_benchmark`: `symbol`, `strategy`, `interval`, `top`, 可选 `initial_cash`, `risk_params`
- `quant_analyze`: `price`, `rsi`, `adx`, `regime`, `news_sentiment`, `tweet_sentiment`, `tweet_count`, `offline`
- `quant_conversation_create`: `channel`, `symbol`, 可选 `title`
- `quant_conversation_context`: `thread_id`
- `quant_conversation_append`: `thread_id`, `role`, `content`

## Returns

所有工具返回 JSON dict 到 `content` field. `details` 字段保留原始结构化数据.

| Tool | 返回字段 |
|---|---|
| `quant_quote` | `price, change, change_percent, volume, day_high, day_low, ...` |
| `quant_kline` | `candles: [{open, high, low, close, volume, timestamp}, ...]` |
| `quant_signals` | `signals: [{description, type, strength}, ...], regime` |
| `quant_news` | `articles: [{title, publisher, link, sentiment_score}, ...]` |
| `quant_sentiment` | `score: [-1, 1], label, article_count` |
| `quant_trending` | `regime, adx, plus_di, minus_di, rsi, ma20_slope, bb_bandwidth` |
| `quant_backtest` | `sharpe, max_drawdown, pnl, win_rate, trades` |
| `quant_benchmark` | `results: [{params, sharpe, ...}, ...]` |
| `quant_analyze` | `signal, confidence, reason, approved, final_action, risk_notes, trend_direction, news_summary` |

## Note

- **标的限定**: symbol-scoped tools 仅支持 9984.T 与 6981.T；其它标的 fail closed。
- **全局情报**: news/sentiment 不是按标的隔离的数据，回答时必须明确这一点。
- **策略边界**: adapter 只传字符串 strategy ID，不包含或推导 Rust 默认参数。
- **数据源**: Yahoo Finance (~15min 延迟, 免费无 Key).
- **语言**: 后端信号描述使用简体中文.
- **价格单位**: JPY.
- **LLM 配额**: `quant_analyze` 默认走 HTTP, 触发 LLM 调用; 受 quota circuit breaker 限制 (90s 冷却窗).
- **Analyze**: `quant_analyze` 只接受 `symbol` 与可选 `question`；行情事实由 Intelligence Plane Gateway 从产品 API 收集。
- **MCP 桥接**: 这些 tool 通过 `@quant-trade/cli-bridge` 调 `uvx quant-trade-agent-tools <subcommand>` 子进程. 子进程超时: 默认 30s, analyze 60s.
