#!/usr/bin/env python3
"""Audit whether a script run produced sufficient logs and cache files.

Reuses _layout.py for all path resolution — do not hard-code paths here.

Usage
-----
    python scripts/audit_run_outputs.py <run_dir> <script_stem> [options]

Arguments
---------
    run_dir         Path to the research run directory.
    script_stem     Script name without .py (e.g. "simulate", "scan_k").

Options
-------
    --log <path>            Explicit log file path.  If omitted, the most
                            recent logs/*-<stem>.log is used.
    --expect-cache <glob>   Cache file path (relative to run_dir) that must
                            exist.  May be repeated.
    --min-numeric <N>       Minimum log lines that contain a numeric value.
                            Default: 3.

Exit codes
----------
    0   PASS  — log present and non-empty, no error file, cache OK
    1   WARN  — log present but thin output, or minor anomaly noted
    2   FAIL  — log missing / empty, error file non-empty, required cache absent
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from _layout import logs_dir, errors_dir, cache_dir  # noqa: E402

# Regex: at least one digit (integer or float)
_NUMERIC_RE = re.compile(r"\d")


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_latest_log(run: Path, stem: str) -> Path | None:
    """Return the most recently modified log file matching *stem*, or None."""
    candidates = sorted(
        logs_dir(run).glob(f"*-{stem}.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _matching_err(log: Path, run: Path) -> Path | None:
    """Return the .err file that shares the timestamp prefix with *log*, if any."""
    # log name format: YYYY-MM-DD-HHMM-<stem>.log
    stem = log.stem          # e.g. "2026-05-16-1430-simulate"
    err_path = errors_dir(run) / (stem + ".err")
    return err_path if err_path.exists() else None


def _count_numeric_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if _NUMERIC_RE.search(line))


# ── main audit logic ──────────────────────────────────────────────────────────

def audit(
    run: Path,
    stem: str,
    log_path: Path | None,
    expect_cache: list[str],
    min_numeric: int,
) -> int:
    """Run all checks.  Prints a structured report.  Returns exit code."""

    overall = 0  # 0=PASS, 1=WARN, 2=FAIL
    lines: list[str] = [f"== Cache-Log Audit: {stem} =="]

    # ── 1. Log file ───────────────────────────────────────────────────────────
    if log_path is None:
        log_path = _find_latest_log(run, stem)

    if log_path is None:
        lines.append(f"Log:   [NOT FOUND]  (searched {logs_dir(run)}/*-{stem}.log)")
        overall = max(overall, 2)
    elif not log_path.exists():
        lines.append(f"Log:   {log_path}  [NOT FOUND]")
        overall = max(overall, 2)
    else:
        size = log_path.stat().st_size
        if size == 0:
            lines.append(f"Log:   {log_path}  [EMPTY — 0 bytes]  → FAIL")
            overall = max(overall, 2)
        else:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            total_lines = text.count("\n")
            num_lines = _count_numeric_lines(text)
            numeric_ok = num_lines >= min_numeric
            numeric_verdict = "PASS" if numeric_ok else "WARN"
            if not numeric_ok:
                overall = max(overall, 1)
            lines.append(f"Log:   {log_path}  [{size} bytes]")
            lines.append(f"  Lines: {total_lines} total, {num_lines} with numeric values")
            lines.append(
                f"  Numeric check: {numeric_verdict}"
                f"  ({num_lines} {'≥' if numeric_ok else '<'} {min_numeric})"
            )
            # Flag if "Traceback" leaked into stdout
            if "Traceback" in text or "Error:" in text:
                lines.append("  WARNING: log contains 'Traceback' or 'Error:' — may indicate mixed stderr")
                overall = max(overall, 1)

    # ── 2. Error file ─────────────────────────────────────────────────────────
    err_path = _matching_err(log_path, run) if log_path else None
    if err_path is None:
        # Also search by stem alone as fallback
        err_candidates = sorted(
            errors_dir(run).glob(f"*-{stem}.err"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        err_path = err_candidates[0] if err_candidates else None

    if err_path is None:
        lines.append("Error: [NOT FOUND — good]")
    else:
        err_content = err_path.read_text(encoding="utf-8", errors="replace").strip()
        if err_content:
            # Show first 5 lines
            excerpt = "\n    ".join(err_content.splitlines()[:5])
            lines.append(f"Error: {err_path}  [NON-EMPTY — FAIL]")
            lines.append(f"  Excerpt:\n    {excerpt}")
            overall = max(overall, 2)
        else:
            lines.append(f"Error: {err_path}  [exists but empty — OK]")

    # ── 3. Cache check ────────────────────────────────────────────────────────
    cache = cache_dir(run)
    if expect_cache:
        lines.append(f"Cache: {cache}/")
        for pattern in expect_cache:
            target = run / pattern
            if target.exists():
                lines.append(f"  {pattern}  [FOUND]")
            else:
                lines.append(f"  {pattern}  [MISSING — FAIL]")
                overall = max(overall, 2)
    else:
        # Just report what's there
        all_cached = list(cache.iterdir()) if cache.exists() else []
        lines.append(f"Cache: {cache}/  [{len(all_cached)} file(s)]")
        if not all_cached:
            lines.append("  (empty — consider caching intermediate arrays for reproducibility)")
            overall = max(overall, 1)

    # ── 4. Summary ────────────────────────────────────────────────────────────
    verdict = {0: "PASS", 1: "WARN", 2: "FAIL"}[overall]
    lines.append(f"\nOverall: {verdict}")
    print("\n".join(lines))
    return overall


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Research run directory.")
    parser.add_argument("script_stem", help="Script stem (filename without .py).")
    parser.add_argument("--log", type=Path, default=None,
                        help="Explicit log file path (overrides auto-search).")
    parser.add_argument("--expect-cache", action="append", default=[],
                        metavar="REL_PATH",
                        help="Cache file path (relative to run_dir) that must exist.")
    parser.add_argument("--min-numeric", type=int, default=3,
                        metavar="N",
                        help="Minimum log lines containing a number (default: 3).")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    run = args.run_dir.resolve()
    return audit(
        run=run,
        stem=args.script_stem,
        log_path=args.log,
        expect_cache=args.expect_cache,
        min_numeric=args.min_numeric,
    )


if __name__ == "__main__":
    sys.exit(main())
