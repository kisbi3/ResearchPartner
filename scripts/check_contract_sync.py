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
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_CONTRACT_WORDS = 2200

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


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def check_word_budget(path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing contract file: {_display(path)}"]

    count = word_count(path.read_text(encoding="utf-8"))
    if count <= MAX_CONTRACT_WORDS:
        return []

    return [
        f"{_display(path)} exceeds resident contract word budget: "
        f"{count} words > {MAX_CONTRACT_WORDS}"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that contract files (AGENTS.md, GEMINI.md) are "
            "byte-identical and within the resident word budget."
        )
    )
    parser.parse_args(argv if argv is not None else [])

    errors: list[str] = []
    for left_rel, right_rel in CONTRACT_PAIRS:
        left = ROOT / left_rel
        right = ROOT / right_rel
        errors.extend(compare_pair(left, right))
        errors.extend(check_word_budget(left))
        errors.extend(check_word_budget(right))

    if errors:
        print("Contract synchronization check failed:")
        for entry in errors:
            print(entry)
        return 1

    print("Contract files are synchronized.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
