#!/usr/bin/env python3
"""PreToolUse hook: ensure Peer-Review Professor spawns originate from a meeting.

The Peer-Review Professor SKILL says: "invoked only within a `meeting` skill
session — never independently." This hook enforces that at spawn time.

When an Agent() call appears to spawn a Peer-Review Professor (detected by
its spawn prompt referencing the role, the meeting skill, or the
peer-review-professor SKILL path), the hook checks that meeting context
exists. Context counts as either:

1. The spawn prompt itself mentions `meeting` and a `--scope review` (or
   `--scope full`) marker, indicating the meeting skill is driving the
   spawn.
2. A meeting artifact `docs/meetings/YYYY-MM-DD-*.md` under the project
   root was created or modified within the last 10 minutes — proving an
   active meeting session. (Layout v3: the project root marked by
   `.research-harness` IS the research root; there is no
   `ResearchPartner-runs/<run>/` wrapper.)

Otherwise the spawn is blocked with exit 2 and a fix message.

Bypass: set ``RESEARCH_HARNESS_BYPASS_MEETING_GATE=1`` for an explicit
one-off waiver.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402

MEETING_FRESHNESS_SECONDS = 10 * 60

PEER_REVIEW_PATTERNS = (
    re.compile(r"\bpeer[-_\s]?review[-_\s]professor\b", re.IGNORECASE),
    re.compile(r"skills/peer-review-professor/SKILL\.md", re.IGNORECASE),
)

MEETING_OK_PATTERNS = (
    re.compile(r"\bmeeting\b.*--scope\s+(review|full)", re.IGNORECASE | re.DOTALL),
    re.compile(r"--scope\s+(review|full).*\bmeeting\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"skills/meeting/SKILL\.md", re.IGNORECASE),
)


def is_peer_review_spawn(prompt: str, subagent_type: str) -> bool:
    if subagent_type and "peer" in subagent_type.lower() and "review" in subagent_type.lower():
        return True
    if not prompt:
        return False
    return any(p.search(prompt) for p in PEER_REVIEW_PATTERNS)


def prompt_indicates_meeting(prompt: str) -> bool:
    if not prompt:
        return False
    return any(p.search(prompt) for p in MEETING_OK_PATTERNS)


def fresh_meeting_exists(project: Path, window: int = MEETING_FRESHNESS_SECONDS) -> tuple[bool, str]:
    """Return (True, reason) when a meeting artifact was touched within `window`.

    Layout v3: meetings live at ``<project_root>/docs/meetings/*.md`` (the
    project root marked by ``.research-harness`` IS the research root — there
    is no ``ResearchPartner-runs/<run>/`` wrapper). The meeting skill,
    ``sync_workflow.py``, and ``generate_workflow_map.py`` all write/read that
    path.
    """
    meetings = project / "docs" / "meetings"
    if not meetings.is_dir():
        return False, "no docs/meetings directory under project root"
    now = time.time()
    for f in meetings.glob("*.md"):
        age = now - f.stat().st_mtime
        if age <= window:
            return True, f"{f.name} (touched {int(age)}s ago)"
    return False, f"no meeting artifact touched within {window}s"


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if payload.get("tool_name", "") != "Agent":
        return 0

    tool_input = payload.get("tool_input", {})
    prompt = tool_input.get("prompt", "") or ""
    description = tool_input.get("description", "") or ""
    subagent_type = tool_input.get("subagent_type", "") or ""
    combined = f"{description}\n{prompt}"

    if not is_peer_review_spawn(combined, subagent_type):
        return 0

    if os.environ.get("RESEARCH_HARNESS_BYPASS_MEETING_GATE") == "1":
        print(
            "PEER-REVIEW BYPASS: spawn allowed via RESEARCH_HARNESS_BYPASS_MEETING_GATE=1",
            file=sys.stderr,
        )
        return 0

    if prompt_indicates_meeting(combined):
        return 0

    try:
        project = project_root_mod.resolve_project(None, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return 0  # not inside a research project — don't block

    ok, reason = fresh_meeting_exists(project)
    if ok:
        return 0

    print(
        f"PEER-REVIEW BLOCK: refused to spawn Peer-Review Professor\n"
        f"  reason: {reason}; spawn prompt does not reference meeting --scope review/full\n"
        f"  rule: Peer-Review Professor is invoked only within a `meeting` skill session\n"
        f"        (see skills/peer-review-professor/SKILL.md and skills/meeting/SKILL.md).\n"
        f"  fix: convene a meeting first — `meeting --scope review --on \"<question>\"`\n"
        f"       (or --scope full), which creates docs/meetings/YYYY-MM-DD-<slug>.md\n"
        f"       and then spawns the Peer-Review Professor as part of the meeting.\n"
        f"  bypass: set RESEARCH_HARNESS_BYPASS_MEETING_GATE=1 for an explicit one-off waiver.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
