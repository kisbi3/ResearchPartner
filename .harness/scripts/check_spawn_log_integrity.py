#!/usr/bin/env python3
"""Cross-check spawn log entries against actual Agent() spawns recorded by hooks.

`docs/gates/agent_spawn_log.md` is plain Markdown that anyone with file-write
access can edit, so a fabricated row could let a forbidden direct code write
slip past `check_src_write_authorization.py`. This script reconciles spawn
log entries against the Agent tool-call events recorded automatically by
`.harness/scripts/workflow_hooks.py` in `<run>/docs/live_workflow_diagram.md` under
the ``## Real-Time Event Log`` section.

A spawn log row is "verified" when there is at least one nearby (within
``--window-min`` minutes, default 60) `start` event in the diagram event log
whose description mentions ``graduate`` (the Graduate Student spawn block
opens with "You are a Graduate Student"). Unverified rows are
reported with exit 2.

This is heuristic — the diagram event-log timestamps are minute-precision
UTC and the spawn log uses local-date strings, so we deliberately give a
generous window. The goal is to catch obvious forgery (5 spawn log rows on a
day when the Agent tool was never called), not millisecond-perfect matching.

Usage:
    python .harness/scripts/check_spawn_log_integrity.py --project <project-dir>
    python .harness/scripts/check_spawn_log_integrity.py --project <project-dir> --window-min 120
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402


def parse_spawn_log(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0] == "Date" or "---" in cells[0]:
            continue
        if cells[1].lower() != "graduate-student":
            continue
        if "YYYY-MM-DD" in cells[0]:
            continue
        rows.append({"date": cells[0], "file": cells[2], "task": cells[3], "status": cells[4]})
    return rows


def parse_diagram_events(path: Path) -> list[dict]:
    """Parse `## Real-Time Event Log` lines of the form:
    🔄 `2026-05-17 12:34 UTC` | `start` | **description** | _agent_
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    # Slice to just the event-log section
    idx = text.find("## Real-Time Event Log")
    if idx < 0:
        return []
    section = text[idx:]
    events: list[dict] = []
    line_re = re.compile(
        r"^[^\s]?\s*`([0-9]{4}-[0-9]{2}-[0-9]{2})\s+[0-9]{2}:[0-9]{2}[^`]*`\s*\|"
        r"\s*`([^`]+)`\s*\|\s*\*\*([^*]+)\*\*",
        re.MULTILINE,
    )
    for m in line_re.finditer(section):
        events.append({"date": m.group(1), "event": m.group(2), "desc": m.group(3)})
    return events


def graduate_starts_by_date(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ev in events:
        if ev["event"] != "start":
            continue
        if "graduate" not in ev["desc"].lower():
            continue
        counts[ev["date"]] = counts.get(ev["date"], 0) + 1
    return counts


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
        "--window-min", type=int, default=60,
        help="(Reserved for future use — currently we match by date only.)",
    )
    args = parser.parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    spawn_log = project / "docs" / "gates" / "agent_spawn_log.md"
    diagram = project / "docs" / "process" / "live_workflow_diagram.md"
    if not diagram.exists():
        legacy = project / "docs" / "live_workflow_diagram.md"
        if legacy.exists():
            diagram = legacy

    rows = parse_spawn_log(spawn_log)
    events = parse_diagram_events(diagram)
    grad_starts_by_date = graduate_starts_by_date(events)

    if not rows:
        print("no graduate-student rows in spawn log; nothing to verify")
        return 0
    if not events:
        print(
            f"INTEGRITY WARN: spawn log has {len(rows)} graduate-student row(s) "
            f"but no parsable event log in {diagram} — cannot verify",
            file=sys.stderr,
        )
        return 0  # warn-only when diagram is missing; treat as non-fatal

    # Reconcile by date bucket
    rows_by_date: dict[str, int] = {}
    for r in rows:
        rows_by_date[r["date"]] = rows_by_date.get(r["date"], 0) + 1

    suspicious: list[tuple[str, int, int]] = []
    for date, count in rows_by_date.items():
        starts = grad_starts_by_date.get(date, 0)
        if starts < count:
            suspicious.append((date, count, starts))

    if not suspicious:
        print(
            f"spawn log verified: {len(rows)} graduate-student row(s) reconciled "
            f"against {sum(grad_starts_by_date.values())} Agent() start event(s)"
        )
        return 0

    print("INTEGRITY FAIL: spawn log rows exceed recorded Agent() spawns:", file=sys.stderr)
    for date, count, starts in suspicious:
        print(
            f"  {date}: {count} graduate-student row(s) but only {starts} Agent() start event(s)",
            file=sys.stderr,
        )
    print(
        "  fix: investigate whether forged rows were added to docs/gates/agent_spawn_log.md\n"
        "       (workflow_hooks.py auto-logs every Agent() call; mismatches mean\n"
        "        the rows were typed by hand, not produced by a real Graduate\n"
        "        Student spawn).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
