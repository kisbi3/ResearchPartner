#!/usr/bin/env python3
"""Claude Code hook entry point for live workflow diagram updates.

Registered in .claude/settings.local.json under PreToolUse and PostToolUse
for the Agent tool. Reads the Claude Code hook JSON from stdin, extracts the
task description, and updates live_workflow_diagram.md.

Exit code 0 always — warnings go to stderr but the tool call is never blocked.
(Enforcement is through PHYSICS.md rules, not hard blocking.)

Usage (set in .claude/settings.local.json):
    python scripts/workflow_hooks.py pre
    python scripts/workflow_hooks.py post
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_workflow_diagram as uwd  # noqa: E402


AGENT_NAME = "lead-agent"
MAX_STEP_LEN = 100


def extract_step(tool_input: dict) -> str:
    """Pull the most descriptive string out of an Agent tool_input dict."""
    step = (
        tool_input.get("description")
        or tool_input.get("prompt", "")[:MAX_STEP_LEN]
        or "unnamed task"
    )
    if isinstance(step, str):
        return step[:MAX_STEP_LEN]
    return "unnamed task"


def run_pre(tool_input: dict) -> None:
    step = extract_step(tool_input)
    diagram_path = uwd.find_active_diagram()

    if diagram_path is None:
        print(
            "WORKFLOW WARNING: No live_workflow_diagram.md found in any ResearchPartner-runs "
            "directory. If this is a research task, run scripts/start_research_run.py first.",
            file=sys.stderr,
        )
        return

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = uwd.update_active_step(content, step, AGENT_NAME)
        content = uwd.append_event(content, "start", step, AGENT_NAME)
        diagram_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"WORKFLOW WARNING: Could not update diagram (pre): {exc}", file=sys.stderr)


def run_post(tool_input: dict) -> None:
    step = extract_step(tool_input)
    diagram_path = uwd.find_active_diagram()

    if diagram_path is None:
        return

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = uwd.append_event(content, "complete", step, AGENT_NAME)
        diagram_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"WORKFLOW WARNING: Could not update diagram (post): {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("pre", "post"):
        print("Usage: workflow_hooks.py <pre|post>", file=sys.stderr)
        return 0  # Never block on bad invocation

    phase = sys.argv[1]

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # Never block on parse failure

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only act on Agent tool calls
    if tool_name != "Agent":
        return 0

    if phase == "pre":
        run_pre(tool_input)
    else:
        run_post(tool_input)

    return 0


if __name__ == "__main__":
    sys.exit(main())
