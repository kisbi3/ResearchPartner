#!/usr/bin/env python3
"""Enforce the Interview Gate at the run level.

The Interview Gate requires that the professor-interview skill output has been
recorded in docs/gates/interview_notes.md before Seed or Execute work begins.

Pass conditions for a given run directory:

1. <run>/docs/gates/interview_notes.md exists; AND
2. The file contains non-placeholder content for all three required fields:
   Crystallized Research Question, Key Assumptions Surfaced, and
   Agreed Direction (i.e. each section has at least one non-empty,
   non-comment line after its heading).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import interview_notes as _interview_notes  # noqa: E402

REQUIRED_SECTIONS = [
    "## Crystallized Research Question",
    "## Key Assumptions Surfaced",
    "## Agreed Direction",
]


def _section_has_content(text: str, heading: str) -> bool:
    """Return True if the section after heading has at least one real line."""
    lines = text.splitlines()
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def check_run(run_dir: Path) -> tuple[int, list[str]]:
    interview = _interview_notes(run_dir)
    if not interview.exists():
        return 1, [
            f"Missing interview notes: {interview}\n"
            "Run the professor-interview skill and record its output in "
            "docs/gates/interview_notes.md before Seed or Execute work begins."
        ]

    text = interview.read_text(encoding="utf-8")
    missing: list[str] = []
    for section in REQUIRED_SECTIONS:
        if not _section_has_content(text, section):
            missing.append(section)

    if missing:
        return 1, [
            "interview_notes.md exists but the following sections are still blank:\n"
            + "\n".join(f"  {s}" for s in missing)
            + "\nFill in these sections using the professor-interview skill output "
            "before proceeding."
        ]

    return 0, ["Interview gate passed: crystallized research question and agreed direction are recorded."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Interview gate for a research run directory."
    )
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="Path to the run directory (must contain docs/gates/interview_notes.md).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    code, messages = check_run(args.run)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
