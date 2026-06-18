#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  libpango-1.0-0 \
  libpangoft2-1.0-0 \
  libcairo2 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  shared-mime-info \
  fonts-dejavu

export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  tmp_uv_install="$(mktemp)"
  curl -LsSf https://astral.sh/uv/install.sh -o "$tmp_uv_install"
  sh "$tmp_uv_install"
  rm "$tmp_uv_install"
fi

uv sync --all-extras

# Dev-only code graph tooling for local indexing.
if ! command -v codegraph >/dev/null 2>&1; then
  sudo npm install -g @colbymchenry/codegraph
fi

bash scripts/install-tectonic.sh
