#!/usr/bin/env python3
"""Bash PRE hook: warn (never block) about orphaned computation checkpoints.

Re-uses ``check_computation_resumable.scan_run`` to detect
``cache/checkpoint_*.pkl`` files left behind by an interrupted prior run.
When the user is about to start a *heavy* Python invocation (same detection
rule as ``check_seed_before_full_run.py``), we print a one-paragraph warning
so they consciously choose between *resuming* the interrupted computation
and *discarding* the stale state.

The script ALWAYS exits 0 — it is informational, not a gate.

Heavy-run detection is duplicated rather than imported to keep this hook
trivially side-effect-free if ``check_seed_before_full_run`` is ever removed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import _project_root as project_root_mod  # noqa: E402

try:
    from check_seed_before_full_run import (  # noqa: E402
        _extract_python_targets,
        _looks_heavy,
    )
    from check_computation_resumable import scan_run  # noqa: E402
except ImportError as exc:
    print(f"warn_orphan_checkpoints: import error — {exc}", file=sys.stderr)
    sys.exit(0)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    command = (payload.get("tool_input", {}) or {}).get("command", "") or ""
    if not command:
        return 0

    targets = _extract_python_targets(command)
    if not any(_looks_heavy(t) for t in targets):
        return 0

    try:
        project = project_root_mod.resolve_project(None, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return 0

    try:
        records = scan_run(project)
    except Exception as exc:
        print(f"warn_orphan_checkpoints: scan failed — {exc}", file=sys.stderr)
        return 0

    orphans = [r for r in records if r.get("likely_orphaned")]
    if not orphans:
        return 0

    head = ", ".join(
        f"{r['stem']} ({r['mtime']})" for r in orphans[:3]
    ) + ("…" if len(orphans) > 3 else "")
    print(
        "ORPHAN CHECKPOINT WARNING: a heavy run is starting but "
        f"{len(orphans)} likely-orphaned checkpoint(s) exist in cache/: "
        f"{head}.\n"
        "  → Resume by loading the checkpoint at startup (see\n"
        "    scripts/run_with_checkpoint.py::CheckpointManager).\n"
        "  → Discard via: python scripts/check_computation_resumable.py "
        "--clear <stem>",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
