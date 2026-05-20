#!/usr/bin/env python3
"""Minimal Claude Code hook for `Agent()` spawn tracking.

Registered in `.claude/settings.local.json` under PreToolUse and
PostToolUse for the Agent tool only. Reads the hook JSON payload from
stdin and maintains the ``## In-Flight Tasks`` table in
``docs/process/live_workflow_diagram.md``.

Why this is the *only* automatic hook left
------------------------------------------
Agent spawns are the one piece of workflow state that leaves no
filesystem trace before completion. If a session is interrupted between
spawn and the sub-agent returning, the spawn vanishes from view. By
recording the row here, we let `check_session_resumable.py` find
abandoned tasks after a cutoff.

Everything else — gates, claims, model versions, papers, figures,
anomalies, lineage edges — is rebuilt on demand by
``scripts/sync_workflow.py`` (the ``/sync-workflow`` skill). There is no
auto-update on Write/Edit/Bash any more.

Exit code 0 always. Outside a research project (no `.research-harness`
marker), this hook is a silent no-op.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _layout as layout  # noqa: E402
import _project_root as project_root_mod  # noqa: E402


AGENT_NAME = "lead-agent"
MAX_STEP_LEN = 100

IN_FLIGHT_HEADER = (
    "## In-Flight Tasks\n\n"
    "<!-- Auto-updated by scripts/workflow_hooks.py on every Agent() spawn. -->\n\n"
    "| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n"
    "|---|---|---|---|---|---|\n"
)

EVENT_EMOJI = {
    "start": "🔄",
    "complete": "✅",
    "error": "❌",
    "spawn": "🚀",
}


def now_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def extract_step(tool_input: dict) -> str:
    """Pull the most descriptive string out of an Agent tool_input dict."""
    step = (
        tool_input.get("description")
        or (tool_input.get("prompt", "") or "")[:MAX_STEP_LEN]
        or "unnamed task"
    )
    if isinstance(step, str):
        return step[:MAX_STEP_LEN]
    return "unnamed task"


def derive_task_id(tool_input: dict) -> str:
    """Deterministic short id derived from the agent's full task input.

    Pre and Post tool-use hooks for the SAME Agent() call receive
    identical ``tool_input`` dicts, so the same hash falls out of each
    invocation and the Post step can find the row that Pre created.

    Format: ``task-<8-char-hash>`` — short enough to read at a glance,
    long enough that accidental collisions across a single project are
    vanishingly rare.
    """
    description = str(tool_input.get("description", ""))
    prompt = str(tool_input.get("prompt", ""))
    subagent = str(tool_input.get("subagent_type", ""))
    digest = hashlib.sha1(
        f"{subagent}\0{description}\0{prompt}".encode("utf-8")
    ).hexdigest()[:8]
    return f"task-{digest}"


def derive_agent_role(tool_input: dict) -> str:
    """Use subagent_type when present; otherwise fall back to a generic role."""
    sub = tool_input.get("subagent_type")
    return str(sub).strip() if sub else "agent"


# ── Markdown helpers ──────────────────────────────────────────────────────────


def _resolve_diagram_path(project: Path) -> Path:
    """Project-local diagram path, scaffolded if absent.

    The scaffold here matches sync_workflow.py's so the two stay
    compatible. If sync_workflow.py runs after this, it will preserve
    the In-Flight Tasks table we just wrote to.
    """
    md = layout.live_workflow_diagram(project)
    md.parent.mkdir(parents=True, exist_ok=True)
    if not md.exists():
        md.write_text(_scaffold(project), encoding="utf-8")
    return md


def _scaffold(project: Path) -> str:
    return (
        f"# Live Workflow Diagram — {project.name}\n\n"
        "Auto-managed by `scripts/sync_workflow.py` (everything except the\n"
        "In-Flight Tasks and Real-Time Event Log sections).\n\n"
        "## Active Step\n\n"
        "- Current step: (not started)\n"
        "- Current owner: lead-agent\n"
        "- Last update: never\n\n"
        "## Gate Status\n\n"
        "| Gate | Status | Note |\n"
        "|---|---|---|\n"
        "| Orient gate | pending |  |\n"
        "| Interview gate | pending |  |\n"
        "| Literature review and replanning | pending |  |\n"
        "| Test-design seed | pending |  |\n"
        "| Baseline or reproduction target | pending |  |\n"
        "| Execution | pending |  |\n"
        "| Visualization | pending |  |\n"
        "| Professor evaluation | pending |  |\n"
        "| Completion conference | pending |  |\n"
        "| User report | pending |  |\n\n"
        + IN_FLIGHT_HEADER + "\n"
        "Allowed in-flight status values: `spawned`, `acknowledged`, `abandoned`.\n\n"
        "## Real-Time Event Log\n\n"
        "<!-- Append-only. Auto-updated by scripts/workflow_hooks.py on every Agent() spawn. -->\n"
    )


def _ensure_in_flight_section(content: str) -> str:
    if "## In-Flight Tasks" in content:
        return content
    if "## Real-Time Event Log" in content:
        return content.replace(
            "## Real-Time Event Log",
            IN_FLIGHT_HEADER + "\n## Real-Time Event Log",
            1,
        )
    return content.rstrip() + "\n\n" + IN_FLIGHT_HEADER + "\n"


def _append_in_flight_row(content: str, task_id: str, agent: str, step: str) -> str:
    content = _ensure_in_flight_section(content)
    row = f"| `{task_id}` | {agent} | {now_str()} | {step} | — | `spawned` |\n"
    pattern = re.compile(
        r"(## In-Flight Tasks\n.*?\|---\|---\|---\|---\|---\|---\|\n)"
        r"((?:\|[^\n]*\|\n)*)",
        flags=re.DOTALL,
    )

    def _replace(m: re.Match) -> str:
        return m.group(1) + m.group(2) + row

    new_content, n = pattern.subn(_replace, content, count=1)
    if n == 0:
        new_content = content.rstrip() + "\n\n" + IN_FLIGHT_HEADER + row + "\n"
    return new_content


def _set_in_flight_status(content: str, task_id: str, status: str) -> str:
    """Find the latest row with `task_id` and status `spawned`, mark it `status`.

    If no matching `spawned` row is found, the content is returned
    unchanged — the post hook silently no-ops when there's nothing to
    update (e.g., pre never fired because the project marker arrived
    mid-session).
    """
    task_id_esc = re.escape(task_id)
    pattern = re.compile(
        rf"(^\|\s*`{task_id_esc}`\s*\|[^\n]*\|\s*)(`spawned`)(\s*\|\s*$)",
        flags=re.MULTILINE,
    )
    # Match the *last* spawned row so back-to-back same-input spawns
    # are paired in FIFO order with their own post events.
    matches = list(pattern.finditer(content))
    if not matches:
        return content
    last = matches[-1]
    return (content[:last.start(2)] + f"`{status}`" + content[last.end(2):])


def _update_active_step(content: str, step: str, agent: str) -> str:
    new_section = (
        "## Active Step\n\n"
        f"- Current step: **{step}**\n"
        f"- Current owner: {agent}\n"
        f"- Last update: {now_str()}\n"
    )
    pattern = re.compile(r"(^## Active Step\s*\n)(.*?)(?=^## |\Z)",
                         flags=re.MULTILINE | re.DOTALL)
    if pattern.search(content):
        return pattern.sub(new_section + "\n", content, count=1)
    return content + "\n\n" + new_section


def _append_event(content: str, event: str, step: str, agent: str) -> str:
    emoji = EVENT_EMOJI.get(event, "•")
    entry = f"\n{emoji} `{now_str()}` | `{event}` | **{step}** | _{agent}_"
    if "## Real-Time Event Log" in content:
        return content.rstrip() + entry + "\n"
    return content.rstrip() + "\n\n## Real-Time Event Log\n" + entry + "\n"


# ── Pre / Post Agent handlers ────────────────────────────────────────────────


def run_pre(tool_input: dict) -> None:
    try:
        project = project_root_mod.find_project_root(start=Path.cwd(), require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return  # Outside a research project — silent no-op.

    step = extract_step(tool_input)
    task_id = derive_task_id(tool_input)
    agent = derive_agent_role(tool_input)
    diagram_path = _resolve_diagram_path(project)

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = _update_active_step(content, step, agent)
        content = _append_in_flight_row(content, task_id, agent, step)
        content = _append_event(content, "spawn", step, agent)
        diagram_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"WORKFLOW WARNING: pre-spawn diagram update failed: {exc}",
              file=sys.stderr)


def run_post(tool_input: dict) -> None:
    try:
        project = project_root_mod.find_project_root(start=Path.cwd(), require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return

    step = extract_step(tool_input)
    task_id = derive_task_id(tool_input)
    agent = derive_agent_role(tool_input)
    diagram_path = layout.live_workflow_diagram(project)
    if not diagram_path.exists():
        return  # Pre never ran (or someone deleted the file); nothing to mark.

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = _set_in_flight_status(content, task_id, "acknowledged")
        content = _append_event(content, "complete", step, agent)
        diagram_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"WORKFLOW WARNING: post-spawn diagram update failed: {exc}",
              file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("pre", "post"):
        print("Usage: workflow_hooks.py <pre|post>", file=sys.stderr)
        return 0  # Never block on bad invocation

    phase = sys.argv[1]

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if payload.get("tool_name", "") != "Agent":
        return 0  # We only care about Agent() now.

    tool_input = payload.get("tool_input", {}) or {}

    if phase == "pre":
        run_pre(tool_input)
    else:
        run_post(tool_input)

    return 0


if __name__ == "__main__":
    sys.exit(main())
