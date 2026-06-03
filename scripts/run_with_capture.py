#!/usr/bin/env python3
"""Run a src/ script and auto-capture stdout → logs/, stderr → errors/.

Usage
-----
    python scripts/run_with_capture.py <run_dir> <script_path> [args...]
    python scripts/run_with_capture.py --quiet <run_dir> <script_path> [args...]

Examples
--------
    python scripts/run_with_capture.py C:/MyProject src/simulate.py
    python scripts/run_with_capture.py . src/scan.py --k 60 --omega0 20
    python scripts/run_with_capture.py --quiet --tail 30 . src/scan.py

Output files (always created)
------------------------------
    <run_dir>/logs/<YYYY-MM-DD-HHMM>-<script_stem>.log   — full stdout
    <run_dir>/errors/<YYYY-MM-DD-HHMM>-<script_stem>.err — stderr (only if non-empty)

The wrapper prints a one-line status summary when the script finishes.

By default it also echoes the full stdout to the terminal. Agents spawned
via Bash/Agent tools should pass ``--quiet`` so the tool result only carries
the status summary + log paths + the last ``--tail N`` stdout lines, not the
entire run. The full stdout is always in the log file regardless of mode.
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
    *,
    quiet: bool = False,
    tail: int = 20,
) -> int:
    """Execute *script* under Python, capturing stdout and stderr.

    Returns the subprocess exit code. When ``quiet`` is True, the full stdout
    is still written to the log file but the terminal output is limited to
    the status summary + log paths + the last ``tail`` stdout lines + a
    stdout line count. This keeps tool-call results compact for agents.
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

    if result.stdout:
        if quiet:
            stdout_lines = result.stdout.splitlines()
            total_lines = len(stdout_lines)
            tail_lines = stdout_lines[-tail:] if tail > 0 else []
            print(f"  stdout: {total_lines} lines (full log at {log_path})")
            if tail_lines:
                print(f"  --- last {len(tail_lines)} stdout line(s) ---")
                for line in tail_lines:
                    print(line)
        else:
            # Echo full stdout so the user sees it in the terminal
            print(result.stdout, end="")

    rc = result.returncode
    status = "OK" if rc == 0 else f"FAILED (exit {rc})"
    print(f"[run_with_capture] {stem} — {status}")
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress full stdout echo; print only the status summary, log "
             "paths, and the last --tail stdout lines.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=20,
        help="When --quiet is set, number of trailing stdout lines to echo (default: 20).",
    )
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
        quiet=args.quiet,
        tail=args.tail,
    )


if __name__ == "__main__":
    sys.exit(main())
