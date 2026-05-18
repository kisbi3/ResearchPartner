#!/usr/bin/env python3
"""Enforce the Orient Gate at the run level.

The Orient Gate requires that the task-intake skill output has been recorded
in docs/gates/orient_note.md before Seed, Execute, or Evaluate work begins.
The exact path is resolved through scripts/_layout.py (orient_note()), so
docstring paths stay in sync with the canonical run layout.

Pass conditions for a given run directory:

1. <run>/docs/gates/orient_note.md exists; AND
2. The file contains non-placeholder content for all four required fields:
   Task Classification, Responsible Role, First Professor Question, and
   Researcher Answer (i.e. each section has at least one non-empty,
   non-comment line after its heading).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import orient_note as _orient_note  # noqa: E402
import _project_root as project_root_mod  # noqa: E402

REQUIRED_SECTIONS = [
    "## Task Classification",
    "## Responsible Role",
    "## First Professor Question",
    "## Researcher Answer",
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
    orient = _orient_note(project_root)
    if not orient.exists():
        return 1, [
            f"Missing orient note: {orient}\n"
            "Run the task-intake skill and record its output in "
            "docs/gates/orient_note.md before Seed, Execute, or Evaluate work begins."
        ]

    text = orient.read_text(encoding="utf-8")
    missing: list[str] = []
    for section in REQUIRED_SECTIONS:
        if not _section_has_content(text, section):
            missing.append(section)

    if missing:
        return 1, [
            "orient_note.md exists but the following sections are still blank:\n"
            + "\n".join(f"  {s}" for s in missing)
            + "\nFill in these sections using the task-intake skill output "
            "before proceeding."
        ]

    return 0, ["Orient gate passed: task classification and first question are recorded."]


# Backward-compat alias retained for one release.
check_run = check_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Orient gate for a research project directory."
    )
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory (must contain docs/gates/orient_note.md). "
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
