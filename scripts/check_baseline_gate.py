#!/usr/bin/env python3
"""Enforce the Baseline Gate at the run level.

The Baseline Gate Hook requires at least one passing baseline (toy model,
known limit, reproduction, conservation check, dimensional case, etc.) before
full-scale interpretation. If the researcher waives the gate, the waiver must
be visible in the live workflow artifact and the claim ceiling must be
lowered to "observation" before any downstream Execute/Evaluate work begins.

Pass conditions for a given run directory:

1. <run>/docs/gates/baseline_registry.md contains a markdown table row with
   Status=pass; OR
2. <run>/docs/gates/baseline_registry.md contains Status=waived AND
   <run>/docs/process/live_workflow_diagram.md contains both "claim ceiling" and
   "observation" (case-insensitive).

All other states fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import (  # noqa: E402
    baseline_registry as _baseline_registry,
    live_workflow_diagram as _live_workflow,
)

VALID_STATUSES = {"planned", "pass", "fail", "partial", "waived"}


def parse_statuses(text: str) -> list[str]:
    """Extract Status column values from any markdown table that has a Status header."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)

    header_idx: int | None = None
    status_idx: int | None = None
    for i, row in enumerate(rows):
        lower = [c.lower() for c in row]
        if "status" in lower:
            header_idx = i
            status_idx = lower.index("status")
            break
    if header_idx is None or status_idx is None:
        return []

    start = header_idx + 1
    if start < len(rows):
        sep = rows[start]
        if sep and all(c and set(c.replace(":", "")) <= set("-") for c in sep):
            start += 1

    out: list[str] = []
    for row in rows[start:]:
        if len(row) <= status_idx:
            continue
        value = row[status_idx].lower()
        if value in VALID_STATUSES:
            out.append(value)
    return out


def check_run(run_dir: Path) -> tuple[int, list[str]]:
    registry = _baseline_registry(run_dir)
    if not registry.exists():
        return 1, [f"Missing baseline registry: {registry}"]

    text = registry.read_text(encoding="utf-8")
    statuses = parse_statuses(text)

    if "pass" in statuses:
        return 0, ["Baseline gate passed: at least one Status=pass entry recorded."]

    if "waived" in statuses:
        live = _live_workflow(run_dir)
        if not live.exists():
            return 1, [
                "Waiver recorded in baseline_registry.md but "
                f"{live} is missing. Waiver requires visible claim-ceiling "
                "demotion in the live workflow."
            ]
        live_text = live.read_text(encoding="utf-8").lower()
        if "claim ceiling" in live_text and "observation" in live_text:
            return 0, [
                "Baseline gate satisfied via waiver: claim ceiling lowered to "
                "observation in live workflow."
            ]
        return 1, [
            "Waiver entry present in baseline_registry.md but "
            "live_workflow_diagram.md does not record 'claim ceiling' and "
            "'observation'. Waiver must lower the claim ceiling visibly before "
            "downstream work proceeds."
        ]

    return 1, [
        f"No Status=pass or Status=waived entry found in {registry}. "
        "Record at least one baseline result (or an explicit waiver with "
        "claim-ceiling demotion) before full-scale interpretation."
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the baseline gate for a research run directory."
    )
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="Path to the run directory (must contain docs/gates/baseline_registry.md).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    code, messages = check_run(args.run)
    for message in messages:
        print(message)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
