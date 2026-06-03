#!/usr/bin/env python3
"""Scan a research run for orphaned computation checkpoints.

An orphaned checkpoint is a ``cache/checkpoint_*.pkl`` file left behind after
a script was interrupted (killed, usage-limit cutoff, OOM, etc.) before it
could call ``CheckpointManager.clear()``.  This script lists such files so
the researcher can decide whether to resume the interrupted computation or
discard the stale checkpoint.

CLI
---
    python scripts/check_computation_resumable.py --project <project_dir>
    python scripts/check_computation_resumable.py --project <project_dir> --json
    python scripts/check_computation_resumable.py --project <project_dir> --clear <stem>

Exit codes
----------
    0 — no likely-orphaned checkpoints found
    1 — one or more likely-orphaned checkpoints found (or an error)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
from _layout import cache_dir, logs_dir  # noqa: E402
import _project_root as project_root_mod  # noqa: E402


def _mtime_str(path: Path) -> str:
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _stem_from_checkpoint(ckpt: Path) -> str:
    """``checkpoint_simulate_scan.pkl`` → ``simulate_scan``."""
    name = ckpt.name
    if name.startswith("checkpoint_") and name.endswith(".pkl"):
        return name[len("checkpoint_") : -len(".pkl")]
    return name


def _has_matching_log(run: Path, stem: str) -> bool:
    """Return True if ``logs/`` contains any ``.log`` file whose name includes *stem*.

    A matching log suggests the script ran to completion at some point after
    the checkpoint was written — the checkpoint may already be superseded.
    """
    log_dir = logs_dir(run)
    if not log_dir.exists():
        return False
    return any(stem in p.name for p in log_dir.iterdir() if p.suffix == ".log")


def scan_run(run: Path) -> list[dict]:
    """Return a list of checkpoint records found in *run*/cache/.

    Each record has keys: run, stem, path, mtime, size_bytes,
    has_matching_log, likely_orphaned.
    """
    cache = cache_dir(run)
    if not cache.exists():
        return []

    records = []
    for ckpt in sorted(cache.glob("checkpoint_*.pkl")):
        stem = _stem_from_checkpoint(ckpt)
        has_log = _has_matching_log(run, stem)
        records.append(
            {
                "run": str(run),
                "stem": stem,
                "path": str(ckpt),
                "mtime": _mtime_str(ckpt),
                "size_bytes": ckpt.stat().st_size,
                "has_matching_log": has_log,
                "likely_orphaned": not has_log,
            }
        )
    return records


def format_report(records: list[dict]) -> str:
    if not records:
        return "No computation checkpoints found."

    lines = ["## Computation Checkpoint Report", ""]
    for rec in records:
        tag = "likely orphaned (no matching log)" if rec["likely_orphaned"] else "log exists"
        lines.append(f"- `{rec['path']}`")
        lines.append(
            f"  stem: {rec['stem']} | modified: {rec['mtime']} | {rec['size_bytes']} bytes | {tag}"
        )
    lines.append("")
    orphaned = sum(1 for r in records if r["likely_orphaned"])
    lines.append(f"{len(records)} checkpoint(s) found, {orphaned} likely orphaned.")
    if orphaned:
        lines.append("")
        lines.append(
            "To resume: import CheckpointManager from scripts/run_with_checkpoint.py "
            "in your src/ script and call ckpt.load() at startup."
        )
        lines.append(
            "To discard: delete the .pkl file or run with "
            "--clear <stem>."
        )
    return "\n".join(lines)


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
        "--json", action="store_true", help="Emit JSON instead of plain text."
    )
    parser.add_argument(
        "--clear",
        metavar="STEM",
        help="Delete cache/checkpoint_<STEM>.pkl for the given --run and exit.",
    )
    args = parser.parse_args(argv)

    # --clear shortcut
    if args.clear:
        try:
            project = project_root_mod.resolve_project(args.project, require=True)
        except project_root_mod.ProjectRootNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        ckpt = cache_dir(project) / f"checkpoint_{args.clear}.pkl"
        if ckpt.exists():
            ckpt.unlink()
            print(f"Cleared {ckpt}")
            return 0
        print(f"No checkpoint found: {ckpt}", file=sys.stderr)
        return 1

    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    runs = [project]

    records: list[dict] = []
    for run in runs:
        records.extend(scan_run(run))

    if args.json:
        print(json.dumps(records, indent=2))
        orphaned = sum(1 for r in records if r["likely_orphaned"])
        return 1 if orphaned else 0

    print(format_report(records))
    orphaned = sum(1 for r in records if r["likely_orphaned"])
    return 1 if orphaned else 0


if __name__ == "__main__":
    sys.exit(main())
