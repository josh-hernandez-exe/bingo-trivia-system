#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

quiet=false
if [[ "${1:-}" == "--quiet" ]]; then
  quiet=true
fi

run_codegraph() {
  if command -v codegraph >/dev/null 2>&1; then
    codegraph "$@"
    return
  fi

  if command -v npm >/dev/null 2>&1; then
    npm exec --yes @colbymchenry/codegraph -- "$@"
    return
  fi

  echo "[codegraph] skipped: neither codegraph nor npm is available"
  return 0
}

if [[ ! -d .codegraph ]]; then
  echo "[codegraph] initializing and creating first index"
  run_codegraph init --index .
  exit 0
fi

if [[ "$quiet" == "true" ]]; then
  run_codegraph sync -q . || run_codegraph index -q .
else
  run_codegraph sync . || run_codegraph index .
fi
