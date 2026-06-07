#!/usr/bin/env python3
"""PreToolUse hook: block direct Write/Edit to code files inside a project.

Cross-tier rule (Model-A lab group): every executable code file in a project
must be written by a spawned Graduate Student — not by the Lead Agent
(professor). This hook enforces that at write time.

Covered extensions: ``.py`` and ``.ipynb`` anywhere under the project root
(marked by ``.research-harness``), except inside ``docs/`` (Markdown notes),
``literature/`` (PDFs and review notes), and ``.harness/scripts/`` / ``tools/`` (vendored
harness tooling, not researcher code). Test code under ``tests/`` IS research
code and is covered. Layout v3: the project root IS the research root — there is
no ``ResearchPartner-runs/<run>/`` wrapper.

The Graduate Student records its activation in
``docs/gates/agent_spawn_log.md`` before touching code. This hook allows the
write only when a graduate-student row for the target file exists *or* the
spawn log was modified within the freshness window (default 10 min) — covering
the case where the row hasn't been written yet but the agent is actively working.

Bypass: set the environment variable ``RESEARCH_HARNESS_BYPASS_SRC_GATE=1``
for a one-off waived write. The bypass is logged to stderr.

Exit codes:
- 0: write allowed (path is not covered code, or authorization OK)
- 2: write blocked (no spawn log entry / no fresh activity)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402

FRESHNESS_SECONDS = 10 * 60  # spawn log must be touched within 10 minutes
COVERED_EXTENSIONS = {".py", ".ipynb"}
# docs/ + literature/ hold notes and PDFs; .harness/scripts/ + tools/ are vendored harness
# tooling, not researcher code. Everything else (src/, tests/, notebooks/, …) is
# research code, cross-tier gated — grad students write it, the professor does not.
EXEMPT_SUBDIRS = {"docs", "literature", "scripts", "tools", ".harness"}
WRITER_ROLE = "graduate-student"


def find_run_root(file_path: Path) -> Path | None:
    """Return the project root if file_path is covered code inside a project.

    Layout v3: the project root (marked by ``.research-harness``) IS the
    research root — there is no ``ResearchPartner-runs/<run>/`` wrapper. Code
    anywhere under the project is covered, except under an exempt top-level
    directory (see ``EXEMPT_SUBDIRS``).
    """
    try:
        project = project_root_mod.find_project_root(file_path, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return None
    try:
        rel = file_path.resolve().relative_to(project)
    except ValueError:
        return None
    top = rel.parts[0] if rel.parts else ""
    if top in EXEMPT_SUBDIRS:
        return None
    return project


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
        if cells[1].lower() != WRITER_ROLE:
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
    if file_path.suffix.lower() not in COVERED_EXTENSIONS:
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
        f"  project: {run_dir}\n"
        f"  reason: {reason}\n"
        f"  rule: the Lead Agent (professor) does not write code.\n"
        f"        Only spawned Graduate Students write .py/.ipynb files inside\n"
        f"        the project (docs/, literature/, .harness/scripts/, tools/ are exempt).\n"
        f"  fix: spawn a Graduate Student (skills/graduate-student/SKILL.md) and\n"
        f"       let it append a row to docs/gates/agent_spawn_log.md before writing.\n"
        f"  bypass: set RESEARCH_HARNESS_BYPASS_SRC_GATE=1 for a one-off waived write.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
