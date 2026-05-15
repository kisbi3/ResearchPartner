#!/usr/bin/env python3
"""Enforce byte-for-byte synchronization of AGENTS.md and GEMINI.md.

The harness contract is duplicated across AGENTS.md (Codex/Copilot/Claude) and
GEMINI.md (Gemini CLI). Drift between the two means different assistants will
operate under different rules, silently violating the synchronization rule
stated in both files. This script blocks that drift.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTRACT_PAIRS = [
    ("AGENTS.md", "GEMINI.md"),
]


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def compare_pair(left: Path, right: Path) -> list[str]:
    if not left.exists():
        return [f"Missing contract file: {_display(left)}"]
    if not right.exists():
        return [f"Missing contract file: {_display(right)}"]

    left_text = left.read_text(encoding="utf-8")
    right_text = right.read_text(encoding="utf-8")
    if left_text == right_text:
        return []

    diff = difflib.unified_diff(
        left_text.splitlines(keepends=True),
        right_text.splitlines(keepends=True),
        fromfile=_display(left),
        tofile=_display(right),
        n=1,
    )
    return ["".join(diff).rstrip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that contract files (AGENTS.md, GEMINI.md) are byte-identical."
    )
    parser.parse_args(argv if argv is not None else [])

    errors: list[str] = []
    for left_rel, right_rel in CONTRACT_PAIRS:
        errors.extend(compare_pair(ROOT / left_rel, ROOT / right_rel))

    if errors:
        print("Contract synchronization check failed:")
        for entry in errors:
            print(entry)
        return 1

    print("Contract files are synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
