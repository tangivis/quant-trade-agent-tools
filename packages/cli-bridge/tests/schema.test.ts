import { describe, it, expect } from "vitest";
import {
  SUPPORTED_INTERVALS,
  SUPPORTED_SYMBOLS,
  TOOL_NAMES,
  TOOL_SCHEMAS,
} from "../src/schema.js";

describe("TOOL_NAMES", () => {
  it("exposes exactly 12 tool names", () => {
    expect(TOOL_NAMES).toHaveLength(12);
  });

  it("contains the expected canonical names in the canonical order", () => {
    expect(TOOL_NAMES).toEqual([
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
    ]);
  });
});

describe("TOOL_SCHEMAS", () => {
  it("has a schema entry for every tool name", () => {
    for (const name of TOOL_NAMES) {
      expect(TOOL_SCHEMAS[name]).toBeDefined();
      expect(TOOL_SCHEMAS[name].name).toBe(name);
    }
  });

  it("every schema has type=object input", () => {
    for (const name of TOOL_NAMES) {
      expect(TOOL_SCHEMAS[name].inputSchema.type).toBe("object");
    }
  });

  it("analyze exposes only the native Gateway inputs", () => {
    expect(Object.keys(TOOL_SCHEMAS.analyze.inputSchema.properties).sort()).toEqual([
      "question",
      "symbol",
    ]);
    expect(TOOL_SCHEMAS.analyze.description).toContain("Native Gateway");
  });

  it("backtest/benchmark require strategy", () => {
    expect(TOOL_SCHEMAS.backtest.inputSchema.required).toContain("strategy");
    expect(TOOL_SCHEMAS.benchmark.inputSchema.required).toContain("strategy");
  });

  it("keeps all symbol-scoped tools on the same enum contract", () => {
    for (const name of ["quote", "kline", "signals", "trending", "backtest", "benchmark", "analyze", "conversation_create"] as const) {
      expect(TOOL_SCHEMAS[name].inputSchema.properties.symbol).toEqual({
        type: "string",
        enum: SUPPORTED_SYMBOLS,
        default: "9984.T",
      });
    }
    for (const name of ["kline", "backtest", "benchmark"] as const) {
      expect(
        (TOOL_SCHEMAS[name].inputSchema.properties.interval as { enum: readonly string[] }).enum,
      ).toEqual(SUPPORTED_INTERVALS);
    }
  });

  it("keeps global news and sentiment free of fake symbol scoping", () => {
    expect(TOOL_SCHEMAS.news.inputSchema.properties).not.toHaveProperty("symbol");
    expect(TOOL_SCHEMAS.sentiment.inputSchema.properties).not.toHaveProperty("symbol");
    expect(TOOL_SCHEMAS.news.description).toContain("global");
    expect(TOOL_SCHEMAS.sentiment.description).toContain("global");
  });

  it("exposes exact backtest forwarding fields", () => {
    for (const name of ["backtest", "benchmark"] as const) {
      expect(TOOL_SCHEMAS[name].inputSchema.properties).toHaveProperty("initial_cash");
      expect(TOOL_SCHEMAS[name].inputSchema.properties).toHaveProperty("risk_params");
    }
    expect(TOOL_SCHEMAS.backtest.inputSchema.properties).toHaveProperty("days");
  });

  it("documents supported strategies without claiming internal imports", () => {
    const backtestStrategy = TOOL_SCHEMAS.backtest.inputSchema.properties.strategy as { enum?: string[] };
    const benchmarkStrategy = TOOL_SCHEMAS.benchmark.inputSchema.properties.strategy as { enum?: string[] };
    expect(backtestStrategy.enum).toContain("vwap");
    expect(benchmarkStrategy.enum).not.toContain("vwap");
    expect(TOOL_SCHEMAS.analyze.description).not.toContain("run_analysis");
  });
});
