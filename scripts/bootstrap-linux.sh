#!/usr/bin/env bash
# Bootstrap a fresh Linux host (Debian/Ubuntu) for running bingo-trivia-system.
set -euo pipefail

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  git curl ca-certificates \
  libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
  libffi-dev shared-mime-info fonts-dejavu

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv sync --all-extras
[[ -f .env ]] || cp .env.example .env
uv run bts doctor
