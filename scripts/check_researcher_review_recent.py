#!/usr/bin/env python3
"""Researcher-review recency gate.

Before the AI promotes a claim or writes a retrospective, there must be a
recent (within --window-hours, default 24h) entry in
``docs/process/researcher_review_log.md`` so we know a human approved the
evidence rather than the AI rubber-stamping its own results.

Reads the standard table:
    | Date | Evidence Shown | Decision | Follow-up |
    | YYYY-MM-DD | ... | ... | ... |

Gate passes when at least one row has Date within the window.

Exit codes (CLI):
    0  gate passes
    1  no recent review — block downstream skill spawn

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


def _parse_review_dates(log_path: Path) -> list[_dt.date]:
    if not log_path.is_file():
        return []
    dates: list[_dt.date] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] == "Date" or "---" in cells[0]:
            continue
        if "YYYY-MM-DD" in cells[0]:
            continue  # template placeholder
        try:
            dates.append(_dt.date.fromisoformat(cells[0]))
        except ValueError:
            continue
    return dates


def check_project(project: Path, window_hours: int = 24) -> tuple[int, list[str]]:
    log = project / "docs" / "process" / "researcher_review_log.md"
    dates = _parse_review_dates(log)
    if not dates:
        return 1, [
            f"No researcher review entries in {log.relative_to(project)} — "
            "the AI cannot promote a claim or close a stage without a recorded "
            "human-review entry. Add a row with today's date stating the "
            "evidence shown and the decision."
        ]
    latest = max(dates)
    age_hours = (_dt.date.today() - latest).days * 24
    if age_hours > window_hours:
        return 1, [
            f"Latest researcher review is {latest} ({age_hours}h ago; window "
            f"is {window_hours}h). Show the researcher current evidence and "
            "record a fresh review row before promoting the claim."
        ]
    return 0, [f"Researcher-review recency gate passed (latest: {latest})."]


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
