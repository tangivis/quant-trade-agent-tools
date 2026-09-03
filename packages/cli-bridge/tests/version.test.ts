import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

const EXPECTED_RELEASE_VERSION = "0.4.0";

function versionAt(relativePath: string): string {
  const manifest = JSON.parse(
    readFileSync(new URL(relativePath, import.meta.url), "utf8"),
  ) as { version: string };
  return manifest.version;
}

describe("release version", () => {
  it("pins the root, bridge, pi and dsh packages to 0.4.0", () => {
    expect([
      versionAt("../../../package.json"),
      versionAt("../package.json"),
      versionAt("../../agent-tools-pi/package.json"),
      versionAt("../../agent-tools-dsh/package.json"),
    ]).toEqual(Array(4).fill(EXPECTED_RELEASE_VERSION));
  });
});
