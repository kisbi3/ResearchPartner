"""Tests for scripts/audit_run_outputs.py.

Covers: log-not-found, empty log, thin log (WARN), good log (PASS),
        non-empty error file (FAIL), missing expected cache (FAIL),
        cache present (PASS), cache empty without expect-cache (WARN).
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from audit_run_outputs import audit  # noqa: E402
from _layout import logs_dir, errors_dir, cache_dir  # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def make_run(tmp_path: Path) -> Path:
    """Create a minimal v2 run directory with empty subdirectories."""
    for sub in ("logs", "errors", "cache", "docs/gates"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    return tmp_path


def write_log(run: Path, stem: str, content: str) -> Path:
    log = logs_dir(run) / f"2026-05-16-1200-{stem}.log"
    log.write_text(content, encoding="utf-8")
    return log


def write_err(run: Path, stem: str, content: str) -> Path:
    err = errors_dir(run) / f"2026-05-16-1200-{stem}.err"
    err.write_text(content, encoding="utf-8")
    return err


# ── tests ─────────────────────────────────────────────────────────────────────

def test_log_not_found_returns_fail(tmp_path):
    run = make_run(tmp_path)
    rc = audit(run, "simulate", log_path=None, expect_cache=[], min_numeric=3)
    assert rc == 2


def test_empty_log_returns_fail(tmp_path):
    run = make_run(tmp_path)
    log = write_log(run, "simulate", "")
    rc = audit(run, "simulate", log_path=log, expect_cache=[], min_numeric=3)
    assert rc == 2


def test_log_with_fewer_numeric_lines_than_threshold_returns_warn(tmp_path):
    run = make_run(tmp_path)
    content = "starting simulation\nno numbers here\nstill no numbers\n"
    log = write_log(run, "simulate", content)
    rc = audit(run, "simulate", log_path=log, expect_cache=[], min_numeric=3)
    assert rc == 1


def test_log_with_sufficient_numeric_lines_returns_pass(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\nelapsed_s = 10.5\n"
    log = write_log(run, "simulate", content)
    # Put a file in cache/ so the auditor does not WARN about an empty cache dir
    (cache_dir(run) / "checkpoint.npy").write_bytes(b"\x93NUMPY")
    rc = audit(run, "simulate", log_path=log, expect_cache=[], min_numeric=3)
    assert rc == 0


def test_nonempty_error_file_returns_fail(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\n"
    log = write_log(run, "simulate", content)
    write_err(run, "simulate", "Traceback (most recent call last):\n  File ...\nValueError: boom\n")
    rc = audit(run, "simulate", log_path=log, expect_cache=[], min_numeric=3)
    assert rc == 2


def test_missing_expected_cache_returns_fail(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\n"
    log = write_log(run, "simulate", content)
    rc = audit(run, "simulate", log_path=log,
               expect_cache=["cache/state_t500.npy"], min_numeric=3)
    assert rc == 2


def test_expected_cache_present_returns_pass(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\n"
    log = write_log(run, "simulate", content)
    cache_file = cache_dir(run) / "state_t500.npy"
    cache_file.write_bytes(b"\x93NUMPY")  # minimal numpy header bytes
    rc = audit(run, "simulate", log_path=log,
               expect_cache=["cache/state_t500.npy"], min_numeric=3)
    assert rc == 0


def test_empty_cache_without_expect_returns_warn(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\n"
    log = write_log(run, "simulate", content)
    # cache/ exists (created by make_run) but is empty
    rc = audit(run, "simulate", log_path=log, expect_cache=[], min_numeric=3)
    assert rc == 1


def test_auto_finds_latest_log_when_no_path_given(tmp_path):
    run = make_run(tmp_path)
    content = "R_plus = 0.82\nR_minus = 0.15\ndelta_R = 0.67\n"
    write_log(run, "simulate", content)
    # No explicit log_path — auditor must search logs/*-simulate.log
    rc = audit(run, "simulate", log_path=None, expect_cache=[], min_numeric=3)
    # cache is empty → WARN (1), NOT FAIL (2)
    assert rc == 1
