import { describe, expect, it, vi } from "vitest";
import { resolve } from "node:path";
import { TOOL_NAMES, TOOL_SCHEMAS } from "@quant-trade/cli-bridge";

type RegisteredTool = {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  timeoutMs?: number;
  output: {
    schema: Record<string, unknown>;
    render: (args: unknown, value: unknown) => unknown[];
  };
  execute: (args: unknown, exec: { signal: AbortSignal }) => Promise<unknown>;
};

async function loadPlugin() {
  return import("../src/plugin.js");
}

function createContext() {
  const registered: RegisteredTool[] = [];
  return {
    registered,
    ctx: {
      tools: {
        register: vi.fn((definition: RegisteredTool) => {
          registered.push(definition);
          return () => {};
        }),
      },
    },
  };
}

describe("agent-tools-dsh plugin", () => {
  it("exports the documented Cordis plugin lifecycle", async () => {
    const plugin = await loadPlugin();
    expect(plugin.name).toBe("quant-trade-agent-tools");
    expect(plugin.inject).toEqual(["tools"]);
    expect(typeof plugin.apply).toBe("function");
  });

  it("registers exactly 12 model-facing tools through ctx.tools", async () => {
    const plugin = await loadPlugin();
    const { ctx, registered } = createContext();
    plugin.apply(ctx as never);

    expect(ctx.tools.register).toHaveBeenCalledTimes(12);
    expect(registered.map((tool) => tool.name)).toEqual(
      TOOL_NAMES.map((name) => `quant_${name}`),
    );
    for (const tool of registered) {
      expect(tool.parameters).toMatchObject({ type: "object" });
      expect(tool.output.schema).toEqual({ type: "object" });
      expect(tool.output.render({}, { ok: true })).toEqual([
        { type: "text", text: '{\n  "ok": true\n}' },
      ]);
      expect(typeof tool.execute).toBe("function");
    }
  });

  it("forwards the harness cancellation signal to the CLI bridge", async () => {
    const plugin = await loadPlugin();
    const { ctx, registered } = createContext();
    plugin.apply(ctx as never);
    const previousCommand = process.env.AGENT_TOOLS_PYTHON_CMD;
    process.env.AGENT_TOOLS_PYTHON_CMD = `node ${resolve(
      import.meta.dir,
      "../../cli-bridge/tests/fixtures/slow.mjs",
    )}`;
    const controller = new AbortController();
    const startedAt = Date.now();
    setTimeout(() => controller.abort(), 50);

    try {
      await expect(
        registered[0]!.execute({}, { signal: controller.signal }),
      ).rejects.toThrow(/aborted/);
      expect(Date.now() - startedAt).toBeLessThan(1_000);
    } finally {
      process.env.AGENT_TOOLS_PYTHON_CMD = previousCommand;
    }
  });

  it("registers the shared multi-symbol parameter snapshots unchanged", async () => {
    const plugin = await loadPlugin();
    const { ctx, registered } = createContext();
    plugin.apply(ctx as never);

    for (const [index, toolName] of TOOL_NAMES.entries()) {
      expect(registered[index]!.parameters).toEqual(TOOL_SCHEMAS[toolName].inputSchema);
    }
  });
});
