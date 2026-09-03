import { describe, expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const packageRoot = resolve(import.meta.dir, "..");

describe("agent-tools-dsh package", () => {
  it("declares an installable dsh bundle and tested peer APIs", async () => {
    const manifest = JSON.parse(
      await readFile(resolve(packageRoot, "package.json"), "utf8"),
    );
    expect(manifest.dsh).toEqual({
      bundle: { patch: "./cordis.patch.yml" },
    });
    expect(manifest.peerDependencies["@deepseek-ai/cordis"]).not.toBe("*");
    expect(manifest.peerDependencies["@deepseek-ai/dsh-tools"]).toBeDefined();
    expect(manifest.files).toContain("cordis.patch.yml");
  });

  it("ships a composition patch that inserts the npm package", async () => {
    const patch = await readFile(resolve(packageRoot, "cordis.patch.yml"), "utf8");
    expect(patch).toContain("insert:");
    expect(patch).toContain("@quant-trade/agent-tools-dsh");
  });
});
