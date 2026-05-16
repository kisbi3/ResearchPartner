#!/usr/bin/env python3
"""Run a src/ script and auto-capture stdout → logs/, stderr → errors/.

Usage
-----
    python scripts/run_with_capture.py <run_dir> <script_path> [args...]

Examples
--------
    python scripts/run_with_capture.py C:/ResearchPartner-runs/my-run src/simulate.py
    python scripts/run_with_capture.py . src/scan.py --k 60 --omega0 20

Output files (always created)
------------------------------
    <run_dir>/logs/<YYYY-MM-DD-HHMM>-<script_stem>.log   — full stdout
    <run_dir>/errors/<YYYY-MM-DD-HHMM>-<script_stem>.err — stderr (only if non-empty)

The wrapper also prints a one-line status summary to the console when the
script finishes, so you can see at a glance whether the run succeeded.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import logs_dir, errors_dir  # noqa: E402


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M")


def run_and_capture(
    run: Path,
    script: Path,
    extra_args: list[str],
) -> int:
    """Execute *script* under Python, capturing stdout and stderr.

    Returns the subprocess exit code.
    """
    ts = _timestamp()
    stem = script.stem

    log_dir = logs_dir(run)
    err_dir = errors_dir(run)
    log_dir.mkdir(parents=True, exist_ok=True)
    err_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{ts}-{stem}.log"
    err_path = err_dir / f"{ts}-{stem}.err"

    cmd = [sys.executable, str(script)] + extra_args
    print(f"[run_with_capture] {' '.join(cmd)}")
    print(f"  stdout → {log_path}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    # Always write stdout log
    log_path.write_text(result.stdout, encoding="utf-8")

    # Write stderr only when non-empty
    stderr_clean = result.stderr.strip()
    if stderr_clean:
        err_path.write_text(result.stderr, encoding="utf-8")
        print(f"  stderr → {err_path}")
    else:
        print("  stderr: (empty)")

    # Echo stdout so the user sees it in the terminal
    if result.stdout:
        print(result.stdout, end="")

    rc = result.returncode
    status = "OK" if rc == 0 else f"FAILED (exit {rc})"
    print(f"[run_with_capture] {stem} — {status}")
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the research run directory (must contain logs/ and errors/).",
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Path to the Python script to run (relative to cwd or absolute).",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Extra arguments forwarded to the script.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.script.exists():
        print(f"Error: script not found: {args.script}", file=sys.stderr)
        return 2

    return run_and_capture(
        run=args.run_dir.resolve(),
        script=args.script.resolve(),
        extra_args=args.extra,
    )


if __name__ == "__main__":
    sys.exit(main())
