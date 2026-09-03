import { describe, it, expect } from "vitest";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { buildCliArgs, spawnQuantCli, timeoutForTool } from "../src/spawn.js";

const repositoryRoot = resolve(import.meta.dir, "../../..");
process.env.AGENT_TOOLS_PYTHON_CMD = `uv run --project ${repositoryRoot} agent-tools`;

describe("spawnQuantCli", () => {
  it("serializes booleans as Click flags", () => {
    expect(buildCliArgs({ offline: true, ignored: false, price: 100 })).toEqual([
      "--offline",
      "--price",
      "100",
    ]);
  });

  it("serializes structured risk parameters as JSON", () => {
    expect(buildCliArgs({ risk_params: { max_position_pct: 0.2 } })).toEqual([
      "--risk-params",
      '{"max_position_pct":0.2}',
    ]);
  });

  it("allows the upstream benchmark grid search to finish", () => {
    expect(timeoutForTool("quote")).toBe(30_000);
    expect(timeoutForTool("analyze")).toBe(60_000);
    expect(timeoutForTool("benchmark")).toBe(1_800_000);
  });

  it("uses Node subprocess APIs in published runtime code", async () => {
    const source = await readFile(resolve(import.meta.dir, "../src/spawn.ts"), "utf8");
    expect(source).toContain('from "node:child_process"');
    expect(source).not.toContain("Bun.");
  });

  it("terminates the child when the caller aborts", async () => {
    const previousCommand = process.env.AGENT_TOOLS_PYTHON_CMD;
    process.env.AGENT_TOOLS_PYTHON_CMD = `node ${resolve(import.meta.dir, "fixtures/slow.mjs")}`;
    const controller = new AbortController();
    const startedAt = Date.now();
    setTimeout(() => controller.abort(), 50);

    try {
      const result = await spawnQuantCli({
        subcommand: "ignored",
        timeoutMs: 5_000,
        signal: controller.signal,
      });
      expect(result.exitCode).toBe(130);
      expect(result.stderr).toContain("aborted");
      expect(Date.now() - startedAt).toBeLessThan(1_000);
    } finally {
      process.env.AGENT_TOOLS_PYTHON_CMD = previousCommand;
    }
  });

  it("invokes uvx with the correct command", async () => {
    const result = await spawnQuantCli({
      subcommand: "--help",
      timeoutMs: 30_000,
    });
    expect(result.exitCode).toBe(0);
  });

  it("parses JSON stdout into an object", async () => {
    const result = await spawnQuantCli({
      subcommand: "--help",
      timeoutMs: 30_000,
    });
    expect(typeof result.stdout).toBe("string");
    expect(result.stdout).toContain("Usage:");
  });

  it("propagates non-zero exit code", async () => {
    const result = await spawnQuantCli({
      subcommand: "nonexistent-subcommand",
      timeoutMs: 10_000,
    });
    expect(result.exitCode).not.toBe(0);
  });

  it("captures stderr", async () => {
    const result = await spawnQuantCli({
      subcommand: "nonexistent-subcommand",
      timeoutMs: 10_000,
    });
    expect(result.stderr).toBeDefined();
  });

  it("respects custom timeout", async () => {
    const start = Date.now();
    const result = await spawnQuantCli({
      subcommand: "analyze",
      args: ["--offline", "--price", "100"],
      timeoutMs: 1_000,
    });
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(10_000);
    expect(result.exitCode).toBeDefined();
  });
});
