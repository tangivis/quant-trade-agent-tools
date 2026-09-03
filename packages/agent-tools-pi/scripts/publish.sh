#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -z "${NPM_TOKEN:-}" ]; then
  echo "Error: NPM_TOKEN environment variable is required"
  echo "  1. Create an npm automation token at https://www.npmjs.com/settings/~/tokens"
  echo "  2. Set NPM_TOKEN in GitLab CI/CD Settings > Variables (masked + protected)"
  echo "  3. Or export NPM_TOKEN=... locally for testing"
  exit 1
fi

./scripts/build.sh

npm publish --access public --tag latest