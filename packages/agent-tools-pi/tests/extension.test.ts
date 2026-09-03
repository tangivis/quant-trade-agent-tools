import { describe, it, expect, vi } from "vitest";
import { TOOL_SCHEMAS } from "@quant-trade/cli-bridge";

describe("agent-tools-pi extension", () => {
  it("default export is a function", async () => {
    const mod = await import("../src/extension.js");
    expect(typeof mod.default).toBe("function");
  });

  it("registers tools via the ExtensionAPI on invocation", async () => {
    const { default: extension } = await import("../src/extension.js");
    const registerTool = vi.fn();
    const registerCommand = vi.fn();
    const fakePi = { registerTool, registerCommand };
    extension(fakePi as any);
    expect(registerTool).toHaveBeenCalled();
  });

  it("registers exactly 9 tools", async () => {
    const { default: extension } = await import("../src/extension.js");
    const registerTool = vi.fn();
    const fakePi = { registerTool, registerCommand: vi.fn() };
    extension(fakePi as any);
    expect(registerTool).toHaveBeenCalledTimes(9);
  });

  it("registers tools with names matching TOOL_NAMES schema", async () => {
    const { default: extension } = await import("../src/extension.js");
    const registerTool = vi.fn();
    const fakePi = { registerTool, registerCommand: vi.fn() };
    extension(fakePi as any);
    const calls = registerTool.mock.calls.map((c: any[]) => c[0]);
    const names = calls.map((t: any) => t.name).sort();
    expect(names).toEqual([
      "quant_analyze",
      "quant_backtest",
      "quant_benchmark",
      "quant_kline",
      "quant_news",
      "quant_quote",
      "quant_sentiment",
      "quant_signals",
      "quant_trending",
    ]);
  });

  it("registers the shared multi-symbol parameter snapshots unchanged", async () => {
    const { default: extension } = await import("../src/extension.js");
    const registerTool = vi.fn();
    extension({ registerTool, registerCommand: vi.fn() } as any);

    for (const [index, name] of Object.keys(TOOL_SCHEMAS).entries()) {
      expect(registerTool.mock.calls[index]![0].parameters).toEqual(
        TOOL_SCHEMAS[name as keyof typeof TOOL_SCHEMAS].inputSchema,
      );
    }
  });
});
