#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  libpango-1.0-0 \
  libpangoft2-1.0-0 \
  libcairo2 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  shared-mime-info \
  fonts-dejavu

uv sync --all-extras

# Dev-only code graph tooling for local indexing.
if ! command -v codegraph >/dev/null 2>&1; then
  sudo npm install -g @colbymchenry/codegraph
fi

bash scripts/install-tectonic.sh
