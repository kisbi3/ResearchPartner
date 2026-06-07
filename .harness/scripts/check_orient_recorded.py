#!/usr/bin/env python3
"""Enforce the Orient Gate at the run level.

The Orient Gate requires that the task-intake skill output has been recorded
in docs/gates/orient_note.md before Seed, Execute, or Evaluate work begins.
The exact path is resolved through .harness/scripts/_layout.py (orient_note()), so
docstring paths stay in sync with the canonical run layout.

Pass conditions for a given run directory:

1. <run>/docs/gates/orient_note.md exists (the lab's proposal); AND
2. It contains non-placeholder content for the three required fields:
   Task Classification, Responsible Role, First Professor Question (each
   section has at least one non-empty, non-comment line after its heading); AND
3. <run>/docs/gates/orient_decision.md has a non-empty ``## Decision`` — the
   researcher's (PI) sign-off. That file is write-blocked for agents, so the
   lab cannot record its own decision (this is the brake).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import orient_note as _orient_note  # noqa: E402
from _layout import orient_decision as _orient_decision  # noqa: E402
import _project_root as project_root_mod  # noqa: E402

REQUIRED_SECTIONS = [
    "## Task Classification",
    "## Responsible Role",
    "## First Professor Question",
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

    # Brake: the lab records the proposal in orient_note.md, but the DECISION is
    # the researcher's (PI) to write in the human-owned orient_decision.md.
    decision = _orient_decision(project_root)
    if not decision.exists() or not _section_has_content(
        decision.read_text(encoding="utf-8"), "## Decision"
    ):
        return 1, [
            "Orient note is recorded, but the researcher's decision is not.\n"
            "  The decision belongs in docs/gates/orient_decision.md (## Decision),\n"
            "  which is write-blocked for agents. Present the proposal in\n"
            "  orient_note.md to the researcher and ask them to record their\n"
            "  decision directly. The gate stays closed until they do."
        ]

    return 0, ["Orient gate passed: proposal recorded and researcher decision signed."]


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
