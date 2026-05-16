#!/usr/bin/env python3
"""Update live_workflow_diagram.md for the active research run.

Called by workflow_hooks.py (Claude Code hooks) and directly by agents.

CLI:
    python scripts/update_workflow_diagram.py \\
        --event start|in_progress|complete|error|blocked \\
        --step "Step description" \\
        --agent "agent-name" \\
        [--gate "Gate Name"] \\
        [--gate-status pending|in_progress|pass|fail|blocked|waived|partial] \\
        [--note "Optional note"] \\
        [--diagram path/to/live_workflow_diagram.md]
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
        candidate = run_dir / "docs" / "live_workflow_diagram.md"
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event", required=True,
        choices=["start", "in_progress", "complete", "error", "blocked"],
    )
    parser.add_argument("--step", required=True, help="Step or task description")
    parser.add_argument("--agent", required=True, help="Agent or owner name")
    parser.add_argument("--gate", default=None, help="Gate name to update in the table")
    parser.add_argument(
        "--gate-status", default=None,
        choices=["pending", "in_progress", "pass", "fail", "blocked", "waived", "partial"],
    )
    parser.add_argument("--note", default="", help="Optional note appended to the event line")
    parser.add_argument(
        "--diagram", type=Path, default=None,
        help="Explicit path to live_workflow_diagram.md (auto-discovered if omitted)",
    )
    args = parser.parse_args(argv)

    diagram_path = args.diagram or find_active_diagram()
    if diagram_path is None or not diagram_path.exists():
        print(
            "ERROR: live_workflow_diagram.md not found. "
            "Run scripts/start_research_run.py first to create a research run.",
            file=sys.stderr,
        )
        return 1

    content = diagram_path.read_text(encoding="utf-8")

    content = update_active_step(content, args.step, args.agent)

    if args.gate and args.gate_status:
        content = update_gate_status(content, args.gate, args.gate_status)

    content = append_event(content, args.event, args.step, args.agent, args.note)

    diagram_path.write_text(content, encoding="utf-8")
    print(f"Updated {diagram_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
