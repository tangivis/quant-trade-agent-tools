import { describe, it, expect } from "vitest";
import { parseQuantOutput, QuantError } from "../src/parse.js";
import type { QuantSpawnResult } from "../src/spawn.js";

const ok = (stdout: string, stderr = ""): QuantSpawnResult => ({
  exitCode: 0,
  stdout,
  stderr,
});

const fail = (exitCode: number, stderr: string): QuantSpawnResult => ({
  exitCode,
  stdout: "",
  stderr,
});

describe("parseQuantOutput", () => {
  it("parses valid JSON stdout into data", () => {
    const r = parseQuantOutput(ok('{"signal":"BUY","confidence":0.7}'));
    expect(r.data).toEqual({ signal: "BUY", confidence: 0.7 });
  });

  it("returns string when stdout is not JSON", () => {
    const r = parseQuantOutput(ok("not json at all"));
    expect(r.data).toBe("not json at all");
  });

  it("returns null for empty stdout", () => {
    const r = parseQuantOutput(ok(""));
    expect(r.data).toBeNull();
  });

  it("returns null for whitespace-only stdout", () => {
    const r = parseQuantOutput(ok("   \n  "));
    expect(r.data).toBeNull();
  });

  it("throws QuantError on non-zero exit code", () => {
    expect(() => parseQuantOutput(fail(1, "something broke"))).toThrow(QuantError);
  });

  it("QuantError carries exitCode and stderr", () => {
    try {
      parseQuantOutput(fail(42, "boom"));
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(QuantError);
      const qe = e as QuantError;
      expect(qe.exitCode).toBe(42);
      expect(qe.stderr).toBe("boom");
      expect(qe.message).toContain("42");
      expect(qe.message).toContain("boom");
    }
  });
});
