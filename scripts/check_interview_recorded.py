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
import _project_root as project_root_mod  # noqa: E402

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


def check_project(project_root: Path) -> tuple[int, list[str]]:
    interview = _interview_notes(project_root)
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


# Backward-compat alias retained for one release.
check_run = check_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Interview gate for a research project directory."
    )
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory (must contain docs/gates/interview_notes.md). "
             "Default: walk up from cwd looking for the `.research-harness` marker. "
             "`--run` kept as alias for one release.",
    )
    args = parser.parse_args(argv if argv is not None else [])
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    code, messages = check_project(project)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
