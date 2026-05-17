#!/usr/bin/env python3
"""Claim-ceiling promotion gate.

Before the Lead Agent promotes a run's claim ceiling above
``observation``, the validation evidence must justify it. This script reads
``<run>/docs/gates/validation_log.md`` (a Markdown table with a Status
column) and counts ``pass`` entries; it refuses promotions whose pass count
is below the threshold for the target ceiling.

Ceilings and thresholds:
    observation     -> 0 pass entries (always allowed)
    interpretation  -> >= 1 pass
    mechanism       -> >= 2 pass
    generalization  -> >= 3 pass

The validation log row format:
    | Date | Check | Target | Status | Evidence |
    | YYYY-MM-DD | toy_model | linear_limit | pass | outputs/toy.png |

Exit codes:
- 0: promotion allowed (or already at observation)
- 2: promotion blocked (insufficient evidence, missing log, or bad input)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THRESHOLDS = {
    "observation": 0,
    "interpretation": 1,
    "mechanism": 2,
    "generalization": 3,
}


def count_pass_entries(log_path: Path) -> int:
    if not log_path.is_file():
        return 0
    n = 0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] == "Date" or "---" in cells[0]:
            continue
        if cells[3].lower() == "pass":
            n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Run directory.")
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        choices=sorted(THRESHOLDS.keys()),
        help="Claim ceiling being promoted to.",
    )
    args = parser.parse_args(argv)

    run_dir = args.run.resolve()
    if not run_dir.is_dir():
        print(f"error: run directory not found: {run_dir}", file=sys.stderr)
        return 2

    target = args.target.lower()
    required = THRESHOLDS[target]
    log = run_dir / "docs" / "gates" / "validation_log.md"
    pass_count = count_pass_entries(log)

    if pass_count >= required:
        print(
            f"claim promotion to '{target}' allowed: "
            f"{pass_count} pass entries (>= {required})"
        )
        return 0

    print(
        f"CLAIM PROMOTION BLOCKED: target='{target}' requires >= {required} "
        f"pass entries in {log}; found {pass_count}.\n"
        f"  fix: run additional validation (toy model / analytical limit / "
        f"reproduction / conservation check) and record a 'pass' row in the "
        f"validation log, or file a waiver and lower the target ceiling.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
