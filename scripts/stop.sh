#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v lsof >/dev/null 2>&1; then
  lsof -ti :8000 | xargs -r kill
fi
