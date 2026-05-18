#!/usr/bin/env python3
"""Claim-ceiling promotion gate.

Before the Lead Agent promotes a run's claim ceiling above
``observation``, the validation evidence must justify it. This script reads
``<run>/docs/gates/validation_log.md`` (a Markdown table with a Status
column) and counts ``pass`` entries; it refuses promotions whose pass count
is below the threshold for the target ceiling.

Ceilings and thresholds (count + diversity):
    observation     -> 0 pass entries (always allowed)
    interpretation  -> >= 1 pass
    mechanism       -> >= 2 pass AND >= 1 baseline-class check
                       (baseline classes: toy_model, reproduction,
                        analytical, conservation, dimensional)
    generalization  -> >= 3 pass spanning >= 2 distinct check categories

The diversity requirement reflects scientific practice: a "mechanism"
claim is stronger than aggregated observations only when it survives at
least one principled sanity check, and a "generalization" claim should
survive on more than one kind of test.

The validation log row format:
    | Date | Check | Target | Status | Evidence |
    | YYYY-MM-DD | toy_model | linear_limit | pass | outputs/toy.png |

The Check cell carries the check category. Recognized baseline-class
labels (case-insensitive, substring match):
    toy_model, toy, reproduction, repro, analytical, analytic,
    conservation, dimensional, dimensions, known_limit

Exit codes:
- 0: promotion allowed (or already at observation)
- 2: promotion blocked (insufficient evidence, missing log, or bad input)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402

THRESHOLDS = {
    "observation": 0,
    "interpretation": 1,
    "mechanism": 2,
    "generalization": 3,
}

BASELINE_CLASS_KEYWORDS = (
    "toy_model", "toy", "reproduction", "repro",
    "analytical", "analytic", "conservation",
    "dimensional", "dimensions", "known_limit",
)


def parse_pass_entries(log_path: Path) -> list[str]:
    """Return the Check (category) cell of each pass row."""
    if not log_path.is_file():
        return []
    checks: list[str] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] == "Date" or "---" in cells[0]:
            continue
        if cells[3].lower() == "pass":
            checks.append(cells[1].lower())
    return checks


def has_baseline_class(checks: list[str]) -> bool:
    return any(any(kw in c for kw in BASELINE_CLASS_KEYWORDS) for c in checks)


def distinct_check_count(checks: list[str]) -> int:
    return len({c for c in checks if c})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory. Default: walk up from cwd looking for "
             "the `.research-harness` marker. `--run` kept as alias for one release.",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        choices=sorted(THRESHOLDS.keys()),
        help="Claim ceiling being promoted to.",
    )
    args = parser.parse_args(argv)

    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    target = args.target.lower()
    required = THRESHOLDS[target]
    log = project / "docs" / "gates" / "validation_log.md"
    checks = parse_pass_entries(log)
    pass_count = len(checks)

    # Count gate
    if pass_count < required:
        print(
            f"CLAIM PROMOTION BLOCKED: target='{target}' requires >= {required} "
            f"pass entries in {log}; found {pass_count}.\n"
            f"  fix: run additional validation (toy model / analytical limit / "
            f"reproduction / conservation check) and record a 'pass' row in the "
            f"validation log, or file a waiver and lower the target ceiling.",
            file=sys.stderr,
        )
        return 2

    # Diversity gates for mechanism / generalization
    if target == "mechanism" and not has_baseline_class(checks):
        print(
            f"CLAIM PROMOTION BLOCKED: target='mechanism' requires at least one "
            f"baseline-class pass entry (Check column matching toy_model | "
            f"reproduction | analytical | conservation | dimensional). Pass-row "
            f"Check values found: {sorted(set(checks)) or '[]'}.\n"
            f"  fix: add a baseline reproduction or analytical-limit check and "
            f"record a 'pass' row, or lower the target ceiling to 'interpretation'.",
            file=sys.stderr,
        )
        return 2

    if target == "generalization" and distinct_check_count(checks) < 2:
        print(
            f"CLAIM PROMOTION BLOCKED: target='generalization' requires >= 2 "
            f"distinct check categories among pass rows. Found only "
            f"{distinct_check_count(checks)} distinct category in: "
            f"{sorted(set(checks)) or '[]'}.\n"
            f"  fix: add a pass entry from a different check category (e.g. add a "
            f"conservation check on top of a toy-model reproduction), or lower the "
            f"target ceiling to 'mechanism'.",
            file=sys.stderr,
        )
        return 2

    extras = []
    if target == "mechanism":
        extras.append("baseline-class present")
    if target == "generalization":
        extras.append(f"{distinct_check_count(checks)} distinct check categories")
    extras_str = f"; {', '.join(extras)}" if extras else ""
    print(
        f"claim promotion to '{target}' allowed: {pass_count} pass entries "
        f"(>= {required}){extras_str}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
