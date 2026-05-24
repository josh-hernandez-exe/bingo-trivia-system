#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/bingo-trivia-system

# Ensure the virtual environment exists if the workspace was freshly attached.
if [[ ! -x .venv/bin/python ]]; then
  echo "[post-start] .venv missing; running uv sync --all-extras"
  uv sync --all-extras
fi

# Quick health check so startup surfaces missing optional capabilities.
# This command reports status in a table and is non-fatal for optional deps.
uv run bts doctor || true

# Keep the local code graph index up to date for AI tooling.
bash scripts/codegraph-sync.sh
