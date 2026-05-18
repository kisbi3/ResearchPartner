#!/usr/bin/env python3
"""Update live_workflow_diagram.md for the active research run.

Called by workflow_hooks.py (Claude Code hooks) and directly by agents.

CLI:
    python scripts/update_workflow_diagram.py \\
        --event start|in_progress|complete|error|blocked|spawn|resume \\
        --step "Step description" \\
        --agent "agent-name" \\
        [--gate "Gate Name"] \\
        [--gate-status pending|in_progress|pass|fail|blocked|waived|partial] \\
        [--task-id "task-3-reproduce-guo"] \\
        [--evidence-record "docs/gates/seed_design.md#task-3"] \\
        [--resume-decision continue|retry|abandon] \\
        [--note "Optional note"] \\
        [--diagram path/to/live_workflow_diagram.md]

Spawn/Resume semantics
----------------------
``--event spawn`` records a sub-agent spawn in the ``## In-Flight Tasks``
table with status ``spawned``. ``--event complete`` or ``--event error``
with a matching ``--task-id`` marks the row ``acknowledged``. ``--event
resume`` records a session-resumption event; with ``--task-id`` and
``--resume-decision`` it can mark an in-flight row ``abandoned`` (lost to
interruption / usage-limit cutoff) or leave it ``spawned`` (still expected).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EVENT_EMOJI = {
    "start": "🔄",
    "in_progress": "🔄",
    "complete": "✅",
    "error": "❌",
    "blocked": "⛔",
    "spawn": "🚀",
    "resume": "↩",
}

GATE_STATUS_EMOJI = {
    "pending": "",
    "in_progress": " 🔄",
    "pass": " ✓",
    "fail": " ❌",
    "blocked": " ⛔",
    "waived": " ⚠",
    "partial": " ◑",
}

IN_FLIGHT_HEADER = (
    "## In-Flight Tasks\n\n"
    "<!-- Auto-updated by scripts/update_workflow_diagram.py via "
    "--event spawn / complete / error / resume. "
    "Rows in `spawned` state at session start are candidate abandoned tasks. -->\n\n"
    "| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n"
    "|---|---|---|---|---|---|\n"
)

IN_FLIGHT_STATUSES = {"spawned", "acknowledged", "abandoned"}


def find_runs_root() -> Path | None:
    """Search candidate parent directories for a ResearchPartner-runs folder."""
    for parent in list(ROOT.parents)[:6]:
        candidate = parent / "ResearchPartner-runs"
        if candidate.is_dir():
            return candidate
    return None


def find_active_diagram() -> Path | None:
    """Return live_workflow_diagram.md from the most recently modified run directory."""
    runs_root = find_runs_root()
    if runs_root is None:
        return None
    run_dirs = sorted(
        [d for d in runs_root.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for run_dir in run_dirs:
        for relative in (
            Path("docs") / "process" / "live_workflow_diagram.md",
            Path("docs") / "live_workflow_diagram.md",
        ):
            candidate = run_dir / relative
            if candidate.exists():
                return candidate
    return None


def now_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def update_active_step(content: str, step: str, agent: str) -> str:
    """Replace the content of the ## Active Step section."""
    new_section = (
        f"## Active Step\n\n"
        f"- Current step: **{step}**\n"
        f"- Current owner: {agent}\n"
        f"- Last update: {now_str()}\n"
    )
    return re.sub(
        r"(^## Active Step\s*\n)(.*?)(?=^## |\Z)",
        new_section + "\n",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )


def update_gate_status(content: str, gate: str, status: str) -> str:
    """Update the status cell in the matching Gate Status table row."""
    emoji = GATE_STATUS_EMOJI.get(status, "")
    gate_escaped = re.escape(gate)

    def replace_row(m: re.Match) -> str:
        prefix = m.group(1)   # "| Gate Name |"
        suffix = m.group(3)   # "| note |"
        return f"{prefix} `{status}`{emoji} {suffix}"

    pattern = rf"(\|\s*{gate_escaped}\s*\|)([^|]*)(\|[^|\n]*\|)"
    return re.sub(pattern, replace_row, content)


def append_event(content: str, event: str, step: str, agent: str, note: str = "") -> str:
    """Append a timestamped line to ## Real-Time Event Log (creates section if absent)."""
    emoji = EVENT_EMOJI.get(event, "•")
    ts = now_str()
    note_str = f" — {note}" if note else ""
    entry = f"\n{emoji} `{ts}` | `{event}` | **{step}** | _{agent}_{note_str}"

    section_header = "\n\n## Real-Time Event Log\n"
    if "## Real-Time Event Log" in content:
        return content.rstrip() + entry + "\n"
    else:
        return content.rstrip() + section_header + entry + "\n"


def _ensure_in_flight_section(content: str) -> str:
    """Return content with the ## In-Flight Tasks section present (inserted before
    ## Real-Time Event Log when possible, else appended)."""
    if "## In-Flight Tasks" in content:
        return content

    block = "\n\n" + IN_FLIGHT_HEADER.rstrip() + "\n"
    if "## Real-Time Event Log" in content:
        return content.replace(
            "## Real-Time Event Log",
            IN_FLIGHT_HEADER.rstrip() + "\n\n## Real-Time Event Log",
            1,
        )
    return content.rstrip() + block


def add_in_flight_row(
    content: str,
    task_id: str,
    agent: str,
    step: str,
    evidence_record: str,
) -> str:
    """Append a new row to ## In-Flight Tasks for a fresh spawn event."""
    content = _ensure_in_flight_section(content)
    row = (
        f"| `{task_id}` | {agent} | {now_str()} | {step} | "
        f"{evidence_record or '—'} | `spawned` |\n"
    )

    pattern = re.compile(
        r"(## In-Flight Tasks\n.*?\|---\|---\|---\|---\|---\|---\|\n)"
        r"((?:\|[^\n]*\|\n)*)",
        flags=re.DOTALL,
    )

    def replace(match: re.Match) -> str:
        header, body = match.group(1), match.group(2)
        return header + body + row

    new_content, n = pattern.subn(replace, content, count=1)
    if n == 0:
        # Fallback: rebuild a fresh section at end
        new_content = (
            content.rstrip()
            + "\n\n"
            + IN_FLIGHT_HEADER
            + row
        )
    return new_content


def set_in_flight_status(content: str, task_id: str, status: str) -> tuple[str, bool]:
    """Update the Status cell of the row whose Task ID matches *task_id*.

    Returns (new_content, matched). When no row matches, content is returned
    unchanged with matched=False so the caller can decide whether to warn.
    """
    if status not in IN_FLIGHT_STATUSES:
        raise ValueError(f"Unknown in-flight status: {status}")

    task_id_escaped = re.escape(task_id)
    pattern = re.compile(
        rf"(^\|\s*`{task_id_escaped}`\s*\|[^\n]*\|\s*)(`[^`]*`|[^|\n]*)(\s*\|\s*$)",
        flags=re.MULTILINE,
    )

    matched = {"hit": False}

    def replace(match: re.Match) -> str:
        matched["hit"] = True
        prefix, _old, suffix = match.group(1), match.group(2), match.group(3)
        return f"{prefix}`{status}`{suffix}"

    new_content = pattern.sub(replace, content, count=1)
    return new_content, matched["hit"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event", required=True,
        choices=[
            "start", "in_progress", "complete", "error", "blocked",
            "spawn", "resume",
        ],
    )
    parser.add_argument("--step", required=True, help="Step or task description")
    parser.add_argument("--agent", required=True, help="Agent or owner name")
    parser.add_argument("--gate", default=None, help="Gate name to update in the table")
    parser.add_argument(
        "--gate-status", default=None,
        choices=["pending", "in_progress", "pass", "fail", "blocked", "waived", "partial"],
    )
    parser.add_argument(
        "--task-id", default=None,
        help="Stable identifier for an in-flight sub-agent task "
             "(required for --event spawn; optional for complete/error/resume).",
    )
    parser.add_argument(
        "--evidence-record", default="",
        help="Path or anchor where the spawned task should write its evidence "
             "(used by --event spawn).",
    )
    parser.add_argument(
        "--resume-decision", default=None,
        choices=["continue", "retry", "abandon"],
        help="When --event is resume and --task-id is given, mark how the "
             "researcher decided to handle the in-flight row.",
    )
    parser.add_argument("--note", default="", help="Optional note appended to the event line")
    parser.add_argument(
        "--diagram", type=Path, default=None,
        help="Explicit path to live_workflow_diagram.md (auto-discovered if omitted)",
    )
    args = parser.parse_args(argv)

    if args.event == "spawn" and not args.task_id:
        print(
            "ERROR: --event spawn requires --task-id so the in-flight task can "
            "later be matched to its completion event.",
            file=sys.stderr,
        )
        return 2

    diagram_path = args.diagram or find_active_diagram()
    if diagram_path is None or not diagram_path.exists():
        print(
            "ERROR: live_workflow_diagram.md not found. "
            "Run scripts/init_research_project.py first to scaffold the project.",
            file=sys.stderr,
        )
        return 1

    content = diagram_path.read_text(encoding="utf-8")

    content = update_active_step(content, args.step, args.agent)

    if args.gate and args.gate_status:
        content = update_gate_status(content, args.gate, args.gate_status)

    if args.event == "spawn":
        content = add_in_flight_row(
            content,
            task_id=args.task_id,
            agent=args.agent,
            step=args.step,
            evidence_record=args.evidence_record,
        )

    if args.event in ("complete", "error") and args.task_id:
        content, matched = set_in_flight_status(content, args.task_id, "acknowledged")
        if not matched:
            print(
                f"WARNING: no in-flight row for task-id '{args.task_id}'; "
                "event logged but no row updated.",
                file=sys.stderr,
            )

    if args.event == "resume" and args.task_id and args.resume_decision:
        new_status = (
            "abandoned" if args.resume_decision in ("abandon", "retry") else "spawned"
        )
        content, matched = set_in_flight_status(content, args.task_id, new_status)
        if not matched:
            print(
                f"WARNING: no in-flight row for task-id '{args.task_id}'; "
                "resume decision logged but no row updated.",
                file=sys.stderr,
            )

    content = append_event(content, args.event, args.step, args.agent, args.note)

    diagram_path.write_text(content, encoding="utf-8")
    print(f"Updated {diagram_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
