#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUT_DIR="dist"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

bun build ./src/extension.ts \
  --target node \
  --format esm \
  --outdir "$OUT_DIR" \
  --external "@earendil-works/pi-coding-agent" \
  --minify \
  --sourcemap=inline

echo "Built packages/agent-tools-pi -> $OUT_DIR/"
ls -la "$OUT_DIR"
