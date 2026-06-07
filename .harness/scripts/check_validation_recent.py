#!/usr/bin/env python3
"""Validation-recency gate — require at least one passing validation entry
within the recent past before a claim-to-evidence or scientific-validator
agent may be spawned.

Reads ``docs/gates/validation_log.md`` (the same Markdown table
``check_claim_promotion.py`` consumes) and looks at the Date column of each
``pass`` row. The gate passes when at least one ``pass`` row has Date within
the last ``--window-hours`` hours (default 24).

The intent is to prevent the AI from promoting a claim by citing
month-old evidence; if it has been a day since the last successful check,
re-run validation before claiming.

Exit codes (CLI):
    0  gate passes
    1  no recent pass entry — block downstream skill spawn

Programmatic entry point:
    check_project(project: Path, window_hours: int = 24) -> (int, list[str])
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402


def _parse_pass_dates(log_path: Path) -> list[_dt.date]:
    """Return the Date cell of every ``pass`` row, parsed to date objects."""
    if not log_path.is_file():
        return []
    dates: list[_dt.date] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] == "Date" or "---" in cells[0]:
            continue
        # The 4th cell (index 3) is the Status column in the
        # check_claim_promotion schema: Date | Check | Target | Status | Evidence
        # The original validation_log_template uses: Date | Command | Result | Evidence
        # Accept either by treating any cell == "pass" (case-insensitive) as pass.
        if not any(c.lower() == "pass" for c in cells[1:]):
            continue
        try:
            dates.append(_dt.date.fromisoformat(cells[0]))
        except ValueError:
            continue
    return dates


def check_project(project: Path, window_hours: int = 24) -> tuple[int, list[str]]:
    log = project / "docs" / "gates" / "validation_log.md"
    dates = _parse_pass_dates(log)
    if not dates:
        return 1, [
            f"No 'pass' entries in {log.relative_to(project)} — "
            "run validation (toy model / analytical limit / reproduction / "
            "conservation check) and record a 'pass' row before promoting a claim."
        ]
    latest = max(dates)
    today = _dt.date.today()
    age_hours = (today - latest).days * 24
    if age_hours > window_hours:
        return 1, [
            f"Most recent pass in validation_log.md is {latest} "
            f"({age_hours}h ago, window is {window_hours}h). "
            "Re-run validation before promoting a claim."
        ]
    return 0, [f"Validation-recency gate passed (latest pass: {latest})."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--window-hours", type=int, default=24)
    args = parser.parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    code, messages = check_project(project, args.window_hours)
    for m in messages:
        print(m)
    return code


if __name__ == "__main__":
    sys.exit(main())
