#!/usr/bin/env python3
"""Enforce the Interview Gate at the run level.

The Interview Gate requires that the professor-interview skill output has been
recorded in docs/gates/interview_notes.md before Seed or Execute work begins.

Pass conditions for a given run directory:

1. <run>/docs/gates/interview_notes.md exists (the lab's record); AND
2. It contains non-placeholder content for the three required fields:
   Crystallized Research Question, Key Assumptions Surfaced, and Agreed
   Direction (each section has a non-empty, non-comment line after its heading); AND
3. <run>/docs/gates/interview_decision.md has a non-empty ``## Decision`` — the
   researcher's (PI) sign-off. That file is write-blocked for agents (the brake).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import interview_notes as _interview_notes  # noqa: E402
from _layout import interview_decision as _interview_decision  # noqa: E402
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

    # Brake: the lab records the interview proposal, but the DECISION (agreed
    # direction sign-off) is the researcher's (PI) to write in the human-owned file.
    decision = _interview_decision(project_root)
    if not decision.exists() or not _section_has_content(
        decision.read_text(encoding="utf-8"), "## Decision"
    ):
        return 1, [
            "Interview notes are recorded, but the researcher's decision is not.\n"
            "  The decision belongs in docs/gates/interview_decision.md (## Decision),\n"
            "  which is write-blocked for agents. Present the crystallized question\n"
            "  and direction to the researcher and ask them to record their decision\n"
            "  directly. The gate stays closed until they do."
        ]

    return 0, ["Interview gate passed: notes recorded and researcher decision signed."]


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
    args = parser.parse_args(argv)
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
