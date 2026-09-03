import { buildCliArgs, spawnQuantCli, parseQuantOutput, timeoutForTool, TOOL_SCHEMAS } from "@quant-trade/cli-bridge";
import type { ToolName } from "@quant-trade/cli-bridge";
import type { Context } from "@deepseek-ai/cordis";
import type { ToolDefinition } from "@deepseek-ai/dsh-tools";

export const name = "quant-trade-agent-tools";
export const inject = ["tools"];

export function apply(ctx: Context): void {
  for (const toolName of Object.keys(TOOL_SCHEMAS) as ToolName[]) {
    ctx.tools.register(buildTool(toolName));
  }
}

function buildTool(toolName: ToolName): ToolDefinition {
  const schema = TOOL_SCHEMAS[toolName];
  return {
    name: `quant_${toolName}`,
    description: schema.description,
    parameters: schema.inputSchema,
    timeoutMs: timeoutForTool(toolName),
    output: {
      schema: { type: "object" },
      render: (_args, value) => [
        { type: "text", text: JSON.stringify(value, null, 2) },
      ],
    },
    execute: async (params, exec) => {
      const args = isRecord(params) ? params : {};
      const result = await spawnQuantCli({
        subcommand: toolName,
        args: buildCliArgs(args),
        timeoutMs: timeoutForTool(toolName),
        signal: exec.signal,
      });
      const parsed = parseQuantOutput(result);
      if (!isRecord(parsed.data)) {
        throw new TypeError(`quant_${toolName} returned a non-object result`);
      }
      return parsed.data;
    },
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
