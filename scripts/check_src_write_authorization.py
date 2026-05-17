#!/usr/bin/env python3
"""PreToolUse hook: block direct Write/Edit to a run's src/*.py.

Cross-tier rule (from docs/orchestration_protocol.md): every src/*.py file
in a research run must be written by a spawned Implementation Agent, not by
the Professor Orchestrator or Graduate Student directly. This hook enforces
that at write time.

The Implementation Agent records its activation in
``<run>/docs/gates/agent_spawn_log.md`` before touching src/. This hook
allows the write only when an implementation row for the target file exists
*or* the spawn log was modified within the freshness window (default 10 min)
— covering the case where the row hasn't been written yet but the agent is
actively working.

Bypass: set the environment variable ``RESEARCH_HARNESS_BYPASS_SRC_GATE=1``
for a one-off waived write. The bypass is logged to stderr.

Exit codes:
- 0: write allowed (path is not under a run's src/, or authorization OK)
- 2: write blocked (no spawn log entry / no fresh activity)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

FRESHNESS_SECONDS = 10 * 60  # spawn log must be touched within 10 minutes


def find_run_root(file_path: Path) -> Path | None:
    """Return the run directory if file_path is under <run>/src/."""
    parts = list(file_path.resolve().parts)
    for i in range(len(parts) - 2):
        if parts[i].lower() == "researchpartner-runs" and i + 2 < len(parts) and parts[i + 2] == "src":
            return Path(*parts[: i + 2])
    return None


def spawn_log_authorizes(run_dir: Path, target_file: Path) -> tuple[bool, str]:
    log = run_dir / "docs" / "gates" / "agent_spawn_log.md"
    if not log.is_file():
        return False, "no docs/gates/agent_spawn_log.md found"

    try:
        rel_target = target_file.resolve().relative_to(run_dir).as_posix()
    except ValueError:
        rel_target = target_file.name

    text = log.read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[1].lower() != "implementation":
            continue
        file_cell = cells[2]
        if file_cell.endswith(target_file.name) or file_cell == rel_target:
            return True, f"matched spawn log entry for {file_cell}"

    age = time.time() - log.stat().st_mtime
    if age <= FRESHNESS_SECONDS:
        return True, f"spawn log touched {int(age)}s ago (within {FRESHNESS_SECONDS}s window)"

    return False, f"no matching entry and spawn log last touched {int(age)}s ago"


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return 0

    file_path_str = payload.get("tool_input", {}).get("file_path", "")
    if not file_path_str:
        return 0

    file_path = Path(file_path_str)
    if file_path.suffix != ".py":
        return 0

    run_dir = find_run_root(file_path)
    if run_dir is None:
        return 0

    if os.environ.get("RESEARCH_HARNESS_BYPASS_SRC_GATE") == "1":
        print(
            f"CROSS-TIER BYPASS: src write to {file_path} allowed via "
            f"RESEARCH_HARNESS_BYPASS_SRC_GATE=1",
            file=sys.stderr,
        )
        return 0

    ok, reason = spawn_log_authorizes(run_dir, file_path)
    if ok:
        return 0

    print(
        f"CROSS-TIER BLOCK: refused to {tool_name} {file_path}\n"
        f"  run: {run_dir}\n"
        f"  reason: {reason}\n"
        f"  fix: spawn an Implementation Agent (skills/implementation-agent/SKILL.md)\n"
        f"       and let it append a row to docs/gates/agent_spawn_log.md before writing.\n"
        f"  bypass: set RESEARCH_HARNESS_BYPASS_SRC_GATE=1 for a one-off waived write.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
