export type ToolName =
  | "quote"
  | "kline"
  | "signals"
  | "news"
  | "sentiment"
  | "trending"
  | "backtest"
  | "benchmark"
  | "analyze"
  | "conversation_create"
  | "conversation_context"
  | "conversation_append";

export const TOOL_NAMES: ToolName[] = [
  "quote",
  "kline",
  "signals",
  "news",
  "sentiment",
  "trending",
  "backtest",
  "benchmark",
  "analyze",
  "conversation_create",
  "conversation_context",
  "conversation_append",
];

export interface ToolSchema {
  name: ToolName;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
}

export const SUPPORTED_STRATEGIES = [
  "ma_cross", "rsi", "bb", "vwap", "volume", "combined", "macd",
  "pivot", "mfi", "linreg", "logistic", "knn", "sentiment_combo",
] as const;

export const BENCHMARK_STRATEGIES = SUPPORTED_STRATEGIES.filter(
  (strategy) => strategy !== "vwap" && strategy !== "pivot",
);

export const SUPPORTED_SYMBOLS = ["9984.T", "6981.T"] as const;
export const SUPPORTED_INTERVALS = ["1m", "5m", "15m", "1h", "1d", "1wk"] as const;

const symbolProperty = {
  type: "string",
  enum: SUPPORTED_SYMBOLS,
  default: "9984.T",
} as const;

const intervalProperty = {
  type: "string",
  enum: SUPPORTED_INTERVALS,
  default: "5m",
} as const;

export const TOOL_SCHEMAS: Record<ToolName, ToolSchema> = {
  quote: {
    name: "quote",
    description: "Fetch current quote snapshot for 9984.T or 6981.T.",
    inputSchema: {
      type: "object",
      properties: { symbol: symbolProperty },
      required: [],
    },
  },
  kline: {
    name: "kline",
    description: "Fetch K-line candles (interval/count).",
    inputSchema: {
      type: "object",
      properties: {
        symbol: symbolProperty,
        interval: intervalProperty,
        count: { type: "integer", default: 100 },
      },
      required: [],
    },
  },
  signals: {
    name: "signals",
    description: "Current active trading signals for 9984.T or 6981.T.",
    inputSchema: {
      type: "object",
      properties: { symbol: symbolProperty },
      required: [],
    },
  },
  news: {
    name: "news",
    description: "global upstream news feed; results are not symbol-isolated.",
    inputSchema: {
      type: "object",
      properties: { count: { type: "integer", default: 10 } },
      required: [],
    },
  },
  sentiment: {
    name: "sentiment",
    description: "global aggregate sentiment; results are not symbol-isolated.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  trending: {
    name: "trending",
    description: "Trend direction + ADX/RSI/regime for 9984.T or 6981.T.",
    inputSchema: {
      type: "object",
      properties: { symbol: symbolProperty },
      required: [],
    },
  },
  backtest: {
    name: "backtest",
    description: "Run single strategy backtest.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: symbolProperty,
        strategy: { type: "string", enum: SUPPORTED_STRATEGIES },
        interval: intervalProperty,
        days: { type: "integer", default: 60 },
        initial_cash: { type: "number", exclusiveMinimum: 0 },
        risk_params: { type: "object", default: {} },
      },
      required: ["strategy"],
    },
  },
  benchmark: {
    name: "benchmark",
    description: "Parameter scan benchmark.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: symbolProperty,
        strategy: { type: "string", enum: BENCHMARK_STRATEGIES },
        interval: intervalProperty,
        top: { type: "integer", default: 20 },
        initial_cash: { type: "number", exclusiveMinimum: 0 },
        risk_params: { type: "object", default: {} },
      },
      required: ["strategy"],
    },
  },
  analyze: {
    name: "analyze",
    description: "Native Gateway analysis from server-collected facts.",
    inputSchema: {
      type: "object",
      properties: {
        symbol: symbolProperty,
        question: { type: "string", minLength: 1, maxLength: 2000 },
      },
      required: [],
    },
  },
  conversation_create: {
    name: "conversation_create",
    description: "Create a product-owned conversation thread shared across Harness clients.",
    inputSchema: {
      type: "object",
      properties: {
        channel: { type: "string", enum: ["chat", "wish"], default: "chat" },
        symbol: symbolProperty,
        title: { type: "string", minLength: 1, maxLength: 200 },
      },
      required: [],
    },
  },
  conversation_context: {
    name: "conversation_context",
    description: "Read a product-owned conversation summary and recent messages.",
    inputSchema: {
      type: "object",
      properties: { thread_id: { type: "string", minLength: 1, maxLength: 128 } },
      required: ["thread_id"],
    },
  },
  conversation_append: {
    name: "conversation_append",
    description: "Append a message to a product-owned conversation thread.",
    inputSchema: {
      type: "object",
      properties: {
        thread_id: { type: "string", minLength: 1, maxLength: 128 },
        role: { type: "string", enum: ["user", "assistant"] },
        content: { type: "string", minLength: 1, maxLength: 8000 },
      },
      required: ["thread_id", "role", "content"],
    },
  },
};
