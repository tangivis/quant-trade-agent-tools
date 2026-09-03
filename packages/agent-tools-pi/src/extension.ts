import type { AgentToolResult, ToolDefinition } from "@earendil-works/pi-coding-agent";
import { buildCliArgs, TOOL_NAMES, TOOL_SCHEMAS, spawnQuantCli, parseQuantOutput, timeoutForTool } from "@quant-trade/cli-bridge";

type ExtensionAPI = {
  registerTool: (tool: ToolDefinition) => void;
  registerCommand?: (cmd: unknown) => void;
};

function buildTool(toolName: keyof typeof TOOL_SCHEMAS): ToolDefinition {
  const schema = TOOL_SCHEMAS[toolName];
  return {
    name: `quant_${toolName}`,
    label: `Quant ${toolName}`,
    description: schema.description,
    parameters: schema.inputSchema,
    execute: async (_toolCallId, params): Promise<AgentToolResult<unknown>> => {
      const args = (params ?? {}) as Record<string, unknown>;
      const result = await spawnQuantCli({
        subcommand: toolName,
        args: buildCliArgs(args),
        timeoutMs: timeoutForTool(toolName),
      });
      const parsed = parseQuantOutput(result);
      return {
        content: [{ type: "text", text: JSON.stringify(parsed.data, null, 2) }],
        details: parsed.data,
      };
    },
  };
}

export default function extension(pi: ExtensionAPI): void {
  for (const name of TOOL_NAMES) {
    pi.registerTool(buildTool(name));
  }
}
