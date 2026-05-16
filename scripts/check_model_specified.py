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
   both "## Physical System" and "## Governing Equations" sections; OR
2. <run>/docs/plan/model_skip_waiver.md exists AND has at least one
   non-empty, non-comment line (the skip reason).

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
)

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


def check_run(run_dir: Path) -> tuple[int, list[str]]:
    waiver = _model_skip_waiver(run_dir)
    if waiver.exists() and _has_real_content(waiver):
        return 0, [
            "Model gate passed via skip waiver. "
            "Claim ceiling is at most 'observation' for this run."
        ]

    spec = _model_spec(run_dir)
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

    return 0, ["Model gate passed: physical system and governing equations are recorded."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Model gate for a research run directory."
    )
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="Path to the run directory (must contain docs/plan/model_spec.md).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    code, messages = check_run(args.run)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
