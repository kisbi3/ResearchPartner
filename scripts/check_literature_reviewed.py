#!/usr/bin/env python3
"""Enforce the Literature Gate at the run level.

The Literature Gate requires that the literature-review-planning skill output
has been recorded in docs/literature_review_plan.md with a "ready" or "waived"
status before model-specification or seed-design work begins.

The gate can also be bypassed by creating docs/literature_skip_waiver.md with
a one-line reason for skipping. This lowers the claim ceiling to at most
"interpretation" for the run.

Pass conditions for a given run directory (any one is sufficient):

1. <run>/docs/literature_review_plan.md exists AND contains a
   "## Literature Gate Status" section with "ready" or "waived"; OR
2. <run>/docs/literature_skip_waiver.md exists AND has at least one
   non-empty, non-comment line (the skip reason).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


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


def _section_contains(text: str, heading: str, keywords: list[str]) -> bool:
    """Return True if the section after heading contains any of the keywords."""
    lines = text.splitlines()
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") or line.startswith("# "):
                break
            if any(kw in line.lower() for kw in keywords):
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
    waiver = run_dir / "docs" / "literature_skip_waiver.md"
    if waiver.exists() and _has_real_content(waiver):
        return 0, [
            "Literature gate passed via skip waiver. "
            "Claim ceiling is at most 'interpretation' for this run."
        ]

    plan = run_dir / "docs" / "literature_review_plan.md"
    if not plan.exists():
        return 1, [
            f"Missing literature review plan: {plan}\n"
            "Run the literature-review-planning skill and record its output, "
            "or create docs/literature_skip_waiver.md with a one-line reason "
            "to skip the literature review."
        ]

    text = plan.read_text(encoding="utf-8")
    heading = "## Literature Gate Status"
    if not _section_has_content(text, heading):
        return 1, [
            "literature_review_plan.md exists but '## Literature Gate Status' "
            "section is missing or blank.\n"
            "Complete the literature-review-planning skill and set the status "
            "to 'ready' or 'waived', or create docs/literature_skip_waiver.md "
            "with a skip reason."
        ]

    if not _section_contains(text, heading, ["ready", "waived"]):
        return 1, [
            "'## Literature Gate Status' exists but does not contain 'ready' or 'waived'.\n"
            "Mark the status as 'ready' (review complete) or 'waived' (with reason) "
            "to proceed to model-specification or seed-design."
        ]

    return 0, ["Literature gate passed: review complete or explicitly waived."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Literature gate for a research run directory."
    )
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="Path to the run directory (must contain docs/literature_review_plan.md).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    code, messages = check_run(args.run)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
