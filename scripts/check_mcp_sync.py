from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github" / "copilot-instructions.md"
TARGETS = (
    ROOT / "AGENTS.md",
    ROOT / ".claude" / "CLAUDE.md",
)
BANNER = (
    "<!-- AUTO-GENERATED from .github/copilot-instructions.md "
    "by scripts/sync-ai-instructions.sh. DO NOT EDIT. -->"
)


def expected_text() -> str:
    return f"{BANNER}\n\n{SOURCE.read_text()}"


def main() -> int:
    expected = expected_text()
    problems: list[str] = []
    for target in TARGETS:
        if not target.exists():
            problems.append(f"missing {target.relative_to(ROOT)}")
            continue
        if target.read_text() != expected:
            problems.append(
                f"out of sync: {target.relative_to(ROOT)} (run scripts/sync-ai-instructions.sh)"
            )

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    print("AI instruction mirrors are in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
