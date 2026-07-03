#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  uv venv
fi
source .venv/bin/activate
uv pip install -r backend/requirements.txt >/dev/null

if [ ! -d frontend/node_modules ]; then
  npm --prefix frontend install
fi

npm --prefix frontend run build >/dev/null
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
