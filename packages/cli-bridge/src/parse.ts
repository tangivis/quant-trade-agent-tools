import type { QuantSpawnResult } from "./spawn.js";

export class QuantError extends Error {
  constructor(
    message: string,
    public readonly exitCode: number,
    public readonly stderr: string,
  ) {
    super(message);
    this.name = "QuantError";
  }
}

export interface ParsedQuantResult {
  exitCode: number;
  data: unknown;
  stderr: string;
  raw: string;
}

export function parseQuantOutput(result: QuantSpawnResult): ParsedQuantResult {
  const { exitCode, stdout, stderr } = result;

  if (exitCode !== 0) {
    throw new QuantError(
      `quant-trade-agent-tools exited with code ${exitCode}: ${stderr.trim() || "(no stderr)"}`,
      exitCode,
      stderr,
    );
  }

  if (!stdout.trim()) {
    return { exitCode, data: null, stderr, raw: stdout };
  }

  try {
    const data = JSON.parse(stdout);
    return { exitCode, data, stderr, raw: stdout };
  } catch {
    return { exitCode, data: stdout, stderr, raw: stdout };
  }
}
