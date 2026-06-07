#!/usr/bin/env python3
"""Detect brownfield adoption mode at the project level.

The harness's gate chain is greenfield-shaped: Orient → Interview → Literature →
Model → Baseline-strategy → Seed → Baseline → ... . When the harness is attached
to research that is *already in progress*, the project already has an implemented
model and existing results, so authoring a fresh model spec / baseline strategy
from scratch is the "false validation story" the onboarding skill warns against.

This module reports whether the project is in ADOPTION MODE: a state the PI opts
into by signing docs/gates/adoption_decision.md (a human-owned, agent-write-
blocked file — the brake). The signed decision records the existing model the PI
accepts and the existing result chosen as the reproduction baseline.

`.harness/scripts/enforce_gate_sequence.py` consults this to treat the Model and
Baseline-strategy gates as satisfied-by-adoption while adoption mode is active.
The Baseline gate (a real reproduction record) and the human Orient/Interview
gates are NOT affected — a claim is still validated only after the chosen result
is actually reproduced.

Pass condition (adoption mode active) for a given project directory:

    <project>/docs/gates/adoption_decision.md exists AND has a non-empty
    ``## Decision`` section (the PI's sign-off — write-blocked for agents).

Any other state means adoption mode is inactive (the normal greenfield gate
chain applies), which `check_project` reports as exit code 1.

Exit codes:
    0  adoption mode active (decision signed)
    1  adoption mode inactive (no signed decision)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import adoption_decision as _adoption_decision  # noqa: E402
import _project_root as project_root_mod  # noqa: E402


def _section_has_content(text: str, heading: str) -> bool:
    """Return True if the section after heading has at least one real line."""
    in_section = False
    for line in text.splitlines():
        if line.strip() == heading:
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") or line.startswith("# "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def is_adoption_mode(project_root: Path) -> bool:
    """True iff a signed adoption decision puts the project in adoption mode."""
    decision = _adoption_decision(project_root)
    if not decision.exists():
        return False
    return _section_has_content(decision.read_text(encoding="utf-8"), "## Decision")


def check_project(project_root: Path) -> tuple[int, list[str]]:
    if is_adoption_mode(project_root):
        return 0, [
            "Adoption mode active: docs/gates/adoption_decision.md is signed. "
            "Model and Baseline-strategy gates are satisfied-by-adoption "
            "(existing model + reproduction baseline accepted by the PI)."
        ]
    return 1, [
        "Adoption mode inactive: no signed docs/gates/adoption_decision.md. "
        "The normal greenfield gate chain applies. If this is an existing "
        "project being onboarded, the lab fills the docs/adoption/* inventory "
        "and the PI signs docs/gates/adoption_decision.md (## Decision)."
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report whether a project is in brownfield adoption mode."
    )
    parser.add_argument(
        "--project",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory. Default: walk up from cwd looking for the "
             "`.research-harness` marker.",
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
