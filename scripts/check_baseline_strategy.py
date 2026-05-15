#!/usr/bin/env python3
"""Enforce the Baseline Strategy Gate at the run level.

The Baseline Strategy Gate requires that the professor-graduate student dialogue
has produced a documented decision (variation or new model) with a specific
verification target before seed-design begins.

Pass conditions for a given run directory (all must hold):

1. <run>/docs/plan/baseline_strategy.md exists.
2. The "## Decision" section contains the word "variation" or "new model".
3. If "variation": the "### Reproduce Pass Criterion" section has non-placeholder
   content.
4. If "new model": the "### Analytical Checkpoint 1" section has non-placeholder
   content under "**Pass criterion:**".

There is no skip waiver for this gate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import baseline_strategy as _baseline_strategy  # noqa: E402


def _section_text(text: str, heading: str) -> str:
    """Return the text content of a section (up to the next same-level heading)."""
    lines = text.splitlines()
    in_section = False
    result: list[str] = []
    heading_prefix = heading.split(" ")[0]  # "##" or "###"
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section:
            # Stop at same or higher level heading
            if line.startswith(heading_prefix + " ") or (
                len(heading_prefix) > 2 and line.startswith(heading_prefix[:-1] + " ")
            ):
                break
            result.append(line)
    return "\n".join(result)


def _has_real_content(text: str) -> bool:
    """Return True if text has at least one non-empty, non-comment, non-placeholder line."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--"):
            continue
        if stripped.startswith("**") and stripped.endswith("**"):
            # Bold label lines like "**Expected result:**" are structure, not content
            continue
        return True
    return False


def _get_decision(text: str) -> str | None:
    """Return 'variation', 'new model', or None if not set."""
    section = _section_text(text, "## Decision").lower()
    if "new model" in section:
        return "new model"
    if "variation" in section:
        return "variation"
    return None


def _variation_target_ok(text: str) -> bool:
    """Return True if the Reproduce Pass Criterion section has real content."""
    section = _section_text(text, "### Reproduce Pass Criterion")
    return _has_real_content(section)


def _new_model_target_ok(text: str) -> bool:
    """Return True if Analytical Checkpoint 1 has a real pass criterion."""
    checkpoint = _section_text(text, "### Analytical Checkpoint 1")
    # Look for "**Pass criterion:**" label followed by content
    lines = checkpoint.splitlines()
    after_label = False
    for line in lines:
        stripped = line.strip()
        if "pass criterion" in stripped.lower():
            after_label = True
            continue
        if after_label:
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def check_run(run_dir: Path) -> tuple[int, list[str]]:
    strategy = _baseline_strategy(run_dir)
    if not strategy.exists():
        return 1, [
            f"Missing baseline strategy: {strategy}\n"
            "Run the baseline-strategy skill (professor-graduate student dialogue) "
            "and record the decision in docs/plan/baseline_strategy.md."
        ]

    text = strategy.read_text(encoding="utf-8")
    decision = _get_decision(text)

    if decision is None:
        return 1, [
            "baseline_strategy.md exists but ## Decision is not set to "
            "'variation' or 'new model'.\n"
            "Complete the baseline-strategy dialogue and fill in the Decision section."
        ]

    if decision == "variation":
        if not _variation_target_ok(text):
            return 1, [
                "Decision is 'variation' but ### Reproduce Pass Criterion is empty.\n"
                "State the specific quantitative criterion for a successful reproduction."
            ]
        return 0, [
            "Baseline Strategy gate passed: variation path — reproduce pass criterion recorded."
        ]

    # decision == "new model"
    if not _new_model_target_ok(text):
        return 1, [
            "Decision is 'new model' but ### Analytical Checkpoint 1 has no pass criterion.\n"
            "State the expected analytical result and what tolerance constitutes success."
        ]
    return 0, [
        "Baseline Strategy gate passed: new model path — analytical checkpoint recorded."
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Baseline Strategy gate for a research run directory."
    )
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="Path to the run directory (must contain docs/plan/baseline_strategy.md).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    code, messages = check_run(args.run)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
