#!/usr/bin/env bash
# Mirror .github/copilot-instructions.md → AGENTS.md and .claude/CLAUDE.md
# so all AI assistants read identical guidance.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/.github/copilot-instructions.md"
BANNER="<!-- AUTO-GENERATED from .github/copilot-instructions.md by scripts/sync-ai-instructions.sh. DO NOT EDIT. -->"

mkdir -p "$ROOT/.claude"

for dst in "$ROOT/AGENTS.md" "$ROOT/.claude/CLAUDE.md"; do
  {
    echo "$BANNER"
    echo
    cat "$SRC"
  } > "$dst"
  echo "wrote $dst"
done
