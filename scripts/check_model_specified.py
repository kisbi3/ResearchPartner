#!/usr/bin/env python3
"""Enforce the Model Gate at the run level.

The Model Gate requires that the model-specification skill output has been
recorded in docs/plan/model_spec.md with physical system and governing equations
defined before seed-design or execute work begins.

The gate can also be bypassed by creating docs/plan/model_skip_waiver.md with
a one-line reason for skipping. This lowers the claim ceiling to at most
"observation" for the run.

Pass conditions for a given run directory (any one is sufficient):

1. <run>/docs/plan/model_spec.md exists AND contains non-placeholder content in
   both "## Physical System" and "## Governing Equations" sections, AND
   <run>/docs/gates/model_decision.md has a non-empty "## Decision" (the
   researcher's sign-off — write-blocked for agents); OR
2. <run>/docs/plan/model_skip_waiver.md exists AND has at least one
   non-empty, non-comment line (the skip reason). The waiver is itself a
   PI-owned, agent-write-blocked file, so it needs no second sign-off.

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import (  # noqa: E402
    model_spec as _model_spec,
    model_skip_waiver as _model_skip_waiver,
    model_decision as _model_decision,
)
import _project_root as project_root_mod  # noqa: E402

REQUIRED_SECTIONS = [
    "## Physical System",
    "## Governing Equations",
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
            if line.startswith("## ") or line.startswith("# "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def _has_real_content(path: Path) -> bool:
    """Return True if the file has at least one non-empty, non-comment line."""
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("#"):
            return True
    return False


def check_project(project_root: Path) -> tuple[int, list[str]]:
    waiver = _model_skip_waiver(project_root)
    if waiver.exists() and _has_real_content(waiver):
        return 0, [
            "Model gate passed via skip waiver. "
            "Claim ceiling is at most 'observation' for this run."
        ]

    spec = _model_spec(project_root)
    if not spec.exists():
        return 1, [
            f"Missing model specification: {spec}\n"
            "Run the model-specification skill and record its output in "
            "docs/plan/model_spec.md, or create docs/plan/model_skip_waiver.md with "
            "a one-line reason to skip model specification."
        ]

    text = spec.read_text(encoding="utf-8")
    missing: list[str] = []
    for section in REQUIRED_SECTIONS:
        if not _section_has_content(text, section):
            missing.append(section)

    if missing:
        return 1, [
            "model_spec.md exists but the following sections are still blank:\n"
            + "\n".join(f"  {s}" for s in missing)
            + "\nFill in these sections using the model-specification skill "
            "before proceeding to seed-design or execute."
        ]

    # Brake: the lab records the model spec, but the DECISION to adopt it is the
    # researcher's (PI) to write in the human-owned model_decision.md. (The skip
    # waiver path above is itself a PI-owned file, so it needs no second sign-off.)
    decision = _model_decision(project_root)
    if not decision.exists() or not _section_has_content(
        decision.read_text(encoding="utf-8"), "## Decision"
    ):
        return 1, [
            "Model spec is recorded, but the researcher's decision is not.\n"
            "  The decision belongs in docs/gates/model_decision.md (## Decision),\n"
            "  which is write-blocked for agents. Present the model spec to the\n"
            "  researcher and ask them to record their decision directly. The gate\n"
            "  stays closed until they do (or use a model_skip_waiver — also PI-owned)."
        ]

    return 0, ["Model gate passed: model spec recorded and researcher decision signed."]


# Backward-compat alias retained for one release.
check_run = check_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Model gate for a research project directory."
    )
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory (must contain docs/plan/model_spec.md). "
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
