#!/usr/bin/env python3
"""Summarize whether the latest run can resume cleanly after an interruption.

When a Claude session is cut off by a usage limit, a network failure, or an
explicit /clear, the next session inherits whatever state was last written to
live_workflow_diagram.md. This script extracts a compact resumption summary
so the Professor Orchestrator can read the current state in one place and
ask the researcher how to handle abandoned sub-agent spawns or blocked gates
before continuing.

Pass conditions for a given run directory:

1. ``live_workflow_diagram.md`` exists; AND
2. No rows in ``## In-Flight Tasks`` have status ``spawned``; AND
3. No rows in ``## Gate Status`` have status ``blocked`` or ``in_progress``.

Any in-flight or in-progress state fails the gate so the orchestrator must
surface it to the researcher before acting.

CLI
---
::

    python scripts/check_session_resumable.py            # auto-discover latest run
    python scripts/check_session_resumable.py --run <path>
    python scripts/check_session_resumable.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import live_workflow_diagram as _live_workflow_diagram  # noqa: E402
import update_workflow_diagram as uwd  # noqa: E402


BLOCKING_GATE_STATUSES = {"blocked", "in_progress"}
BLOCKING_TASK_STATUSES = {"spawned"}


def _strip_backticks(cell: str) -> str:
    """Remove all backticks from *cell* and strip surrounding whitespace.

    The live diagram formats statuses as `` `pass` ✓ `` (text after the closing
    backtick), so naive left/right .strip("`") leaves a stray trailing backtick
    when the next character is non-backtick. Use replace to be robust.
    """
    return cell.replace("`", "").strip()


def _parse_active_step(text: str) -> dict[str, str]:
    """Extract Current step / Current owner / Last update from ## Active Step."""
    section = re.search(
        r"^## Active Step\s*\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    out = {"current_step": "", "current_owner": "", "last_update": ""}
    if not section:
        return out
    body = section.group(1)
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Current step:"):
            out["current_step"] = stripped.split(":", 1)[1].strip().strip("*").strip()
        elif stripped.startswith("- Current owner:"):
            out["current_owner"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- Last update:"):
            out["last_update"] = stripped.split(":", 1)[1].strip()
    return out


def _parse_gate_status(text: str) -> list[dict[str, str]]:
    """Return a list of gate rows: [{name, status, note}, ...]."""
    section = re.search(
        r"^## Gate Status\s*\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section:
        return []

    rows: list[dict[str, str]] = []
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        # Skip header and divider rows
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() in {"gate", "---"} or cells[0].startswith("---"):
            continue
        # Some rows are formatted "| Gate |"; tolerate them.
        name = cells[0]
        status = _strip_backticks(cells[1]).split()[0] if cells[1] else ""
        note = cells[2] if len(cells) > 2 else ""
        rows.append({"name": name, "status": status, "note": note})
    return rows


def _parse_in_flight_tasks(text: str) -> list[dict[str, str]]:
    """Return a list of in-flight rows: [{task_id, agent, spawned, step,
    evidence_record, status}, ...]."""
    section = re.search(
        r"^## In-Flight Tasks\s*\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section:
        return []

    rows: list[dict[str, str]] = []
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        if cells[0].lower() in {"task id"} or cells[0].startswith("---"):
            continue
        rows.append({
            "task_id": _strip_backticks(cells[0]),
            "agent": cells[1],
            "spawned": cells[2],
            "step": cells[3],
            "evidence_record": cells[4],
            "status": _strip_backticks(cells[5]),
        })
    return rows


def _find_diagram(run_dir: Path | None) -> Path | None:
    if run_dir is not None:
        candidate = _live_workflow_diagram(run_dir)
        if candidate.exists():
            return candidate
        legacy = run_dir / "docs" / "live_workflow_diagram.md"
        if legacy.exists():
            return legacy
        return None
    return uwd.find_active_diagram()


def check_run(run_dir: Path | None) -> tuple[int, dict]:
    """Return (exit_code, report). Exit code 0 when resumable, 1 otherwise."""
    diagram = _find_diagram(run_dir)
    if diagram is None or not diagram.exists():
        return 1, {
            "resumable": False,
            "reason": "live_workflow_diagram.md not found",
            "diagram": None,
            "run_dir": str(run_dir) if run_dir else None,
            "active_step": {},
            "in_flight_tasks": [],
            "blocking_gates": [],
        }

    text = diagram.read_text(encoding="utf-8")
    active = _parse_active_step(text)
    gates = _parse_gate_status(text)
    tasks = _parse_in_flight_tasks(text)

    in_flight = [t for t in tasks if t["status"] in BLOCKING_TASK_STATUSES]
    blocking_gates = [g for g in gates if g["status"] in BLOCKING_GATE_STATUSES]

    resumable = not in_flight and not blocking_gates
    reasons: list[str] = []
    if in_flight:
        reasons.append(f"{len(in_flight)} in-flight task(s) still marked 'spawned'")
    if blocking_gates:
        reasons.append(f"{len(blocking_gates)} gate(s) blocked or in_progress")

    report = {
        "resumable": resumable,
        "reason": "; ".join(reasons) if reasons else "clean",
        "diagram": str(diagram),
        "run_dir": str(diagram.parent.parent.parent),
        "active_step": active,
        "in_flight_tasks": in_flight,
        "blocking_gates": blocking_gates,
    }
    return (0 if resumable else 1), report


def format_report(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"Run directory: {report.get('run_dir') or '(not found)'}")
    lines.append(f"Diagram:       {report.get('diagram') or '(missing)'}")

    active = report.get("active_step") or {}
    lines.append(f"Active step:   {active.get('current_step') or '(blank)'}")
    lines.append(f"Active owner:  {active.get('current_owner') or '(blank)'}")
    lines.append(f"Last update:   {active.get('last_update') or '(blank)'}")

    in_flight = report.get("in_flight_tasks") or []
    lines.append("")
    lines.append(f"In-flight tasks (status='spawned'): {len(in_flight)}")
    for task in in_flight:
        lines.append(
            f"  - {task['task_id']} ({task['agent']}) — spawned {task['spawned']}: "
            f"{task['step']}"
        )

    gates = report.get("blocking_gates") or []
    lines.append("")
    lines.append(f"Blocking gates (status in {sorted(BLOCKING_GATE_STATUSES)}): {len(gates)}")
    for gate in gates:
        note = f" — {gate['note']}" if gate.get("note") else ""
        lines.append(f"  - {gate['name']}: {gate['status']}{note}")

    lines.append("")
    if report.get("resumable"):
        lines.append("Resumable: YES — no in-flight tasks, no blocking gates.")
    else:
        lines.append(f"Resumable: NO — {report.get('reason')}")
        lines.append("Suggested next step:")
        lines.append(
            "  For each in-flight task, run "
            "`python scripts/update_workflow_diagram.py --event resume "
            "--step \"...\" --agent \"professor-orchestrator\" --task-id <id> "
            "--resume-decision continue|retry|abandon` after asking the "
            "researcher how to handle it."
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether the latest research run can resume cleanly."
    )
    parser.add_argument(
        "--run", type=Path, default=None,
        help="Explicit run directory. When omitted, the script auto-discovers the "
             "most recently modified run under a sibling ResearchPartner-runs folder.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit a machine-readable JSON report instead of plain text.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    code, report = check_run(args.run)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))

    return code


if __name__ == "__main__":
    sys.exit(main())
