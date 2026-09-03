import { describe, expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

describe("agent-tools-pi package", () => {
  it("declares the tested pi host compatibility range", async () => {
    const manifest = JSON.parse(
      await readFile(resolve(import.meta.dir, "../package.json"), "utf8"),
    );
    expect(manifest.peerDependencies["@earendil-works/pi-coding-agent"]).not.toBe("*");
  });
});
