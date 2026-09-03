import { spawn } from "node:child_process";

export interface QuantSpawnOpts {
  subcommand: string;
  args?: string[];
  stdin?: string;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export interface QuantSpawnResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

const DEFAULT_TIMEOUT_MS = 30_000;

export function timeoutForTool(toolName: string): number {
  if (toolName === "benchmark") return 1_800_000;
  if (toolName === "analyze") return 60_000;
  return DEFAULT_TIMEOUT_MS;
}

export function buildCliArgs(values: Record<string, unknown>): string[] {
  const args: string[] = [];
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null || value === false) continue;
    const flag = `--${key.replace(/_/g, "-")}`;
    args.push(flag);
    if (value !== true) {
      args.push(typeof value === "object" ? JSON.stringify(value) : String(value));
    }
  }
  return args;
}

function buildCommand(subcommand: string, args: string[]): string[] {
  const override = process.env.AGENT_TOOLS_PYTHON_CMD;
  if (override) {
    return [...override.split(/\s+/).filter(Boolean), subcommand, ...args];
  }
  return ["uvx", "quant-trade-agent-tools", subcommand, ...args];
}

export async function spawnQuantCli(opts: QuantSpawnOpts): Promise<QuantSpawnResult> {
  const {
    subcommand,
    args = [],
    stdin,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal,
  } = opts;
  const command = buildCommand(subcommand, args);
  const proc = spawn(command[0]!, command.slice(1), {
    stdio: ["pipe", "pipe", "pipe"],
  });
  let stdout = "";
  let stderr = "";
  let spawnError: Error | undefined;
  let forcedExit: "aborted" | "timeout" | undefined;

  proc.stdout.setEncoding("utf8");
  proc.stderr.setEncoding("utf8");
  proc.stdout.on("data", (chunk: string) => { stdout += chunk; });
  proc.stderr.on("data", (chunk: string) => { stderr += chunk; });
  proc.stdin.end(stdin);

  const exited = new Promise<number>((resolve) => {
    proc.once("error", (error) => {
      spawnError = error;
      resolve(127);
    });
    proc.once("close", (code) => resolve(code ?? 1));
  });

  const terminate = (reason: "aborted" | "timeout") => {
    if (forcedExit !== undefined) return;
    forcedExit = reason;
    proc.kill();
  };
  const abort = () => terminate("aborted");
  const timeout = setTimeout(() => terminate("timeout"), timeoutMs);
  signal?.addEventListener("abort", abort, { once: true });
  if (signal?.aborted) abort();

  const exitCode = await exited;
  clearTimeout(timeout);
  signal?.removeEventListener("abort", abort);

  if (forcedExit === "timeout") {
    return {
      exitCode: 124,
      stdout,
      stderr: appendDiagnostic(stderr, `Process killed after ${timeoutMs}ms timeout`),
    };
  }

  if (forcedExit === "aborted") {
    return {
      exitCode: 130,
      stdout,
      stderr: appendDiagnostic(stderr, "Process aborted by caller"),
    };
  }

  return {
    exitCode,
    stdout,
    stderr: spawnError ? appendDiagnostic(stderr, spawnError.message) : stderr,
  };
}

function appendDiagnostic(stderr: string, diagnostic: string): string {
  return stderr.length === 0 || stderr.endsWith("\n")
    ? `${stderr}${diagnostic}`
    : `${stderr}\n${diagnostic}`;
}
