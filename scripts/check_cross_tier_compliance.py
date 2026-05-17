#!/usr/bin/env python3
"""Stage-gate check: refuse to advance if src/*.py exist without spawn records.

Backstop for the PreToolUse hook (scripts/check_src_write_authorization.py).
Run this before promoting a stage gate (Execute -> Evaluate, or before writing
a Stage Checkpoint with confidence in the produced code).

Exits 2 when verdict == 'warn' (src files exist but spawn log entries are
missing). Exits 0 on pass / unknown / n/a / skipped.

Usage:
    python scripts/check_cross_tier_compliance.py --run <run-dir>
    python scripts/check_cross_tier_compliance.py --run <run-dir> --strict
        # also fail on verdict='unknown' (no spawn log at all)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_stage_checkpoint import detect_cross_tier_compliance  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Run directory.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail when there is no spawn log at all (verdict=unknown).",
    )
    args = parser.parse_args(argv)

    run_dir = args.run.resolve()
    if not run_dir.is_dir():
        print(f"error: run directory not found: {run_dir}", file=sys.stderr)
        return 2

    c = detect_cross_tier_compliance(run_dir)
    verdict = c["verdict"]

    if verdict == "warn":
        print(f"CROSS-TIER FAIL: {c['status']}", file=sys.stderr)
        print(
            f"  src/*.py files: {c['src_count']}\n"
            f"  Implementation Agent spawns: {c['impl_spawns']}\n"
            f"  fix: spawn Implementation Agents for the unrecorded files,\n"
            f"       or add waiver rows to docs/gates/agent_spawn_log.md\n"
            f"       (Role='implementation', Status='waived: <reason>').",
            file=sys.stderr,
        )
        return 2

    if verdict == "unknown" and args.strict:
        print(f"CROSS-TIER FAIL (strict): {c['status']}", file=sys.stderr)
        return 2

    print(f"cross-tier compliance: {c['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
