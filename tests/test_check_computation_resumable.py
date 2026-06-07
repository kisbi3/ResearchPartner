import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "check_computation_resumable.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_computation_resumable", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_computation_resumable"] = module
    spec.loader.exec_module(module)
    return module


def _make_checkpoint(cache_dir: Path, stem: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    ckpt = cache_dir / f"checkpoint_{stem}.pkl"
    import pickle
    ckpt.write_bytes(pickle.dumps({"step": 5}))
    return ckpt


def test_no_checkpoints_returns_empty(tmp_path):
    mod = load_module()
    records = mod.scan_run(tmp_path)
    assert records == []


def test_missing_cache_dir_returns_empty(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    mod = load_module()
    records = mod.scan_run(run)
    assert records == []


def test_checkpoint_file_is_detected(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    _make_checkpoint(cache, "simulate")

    mod = load_module()
    records = mod.scan_run(run)
    assert len(records) == 1
    assert records[0]["stem"] == "simulate"


def test_orphaned_without_log(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    _make_checkpoint(cache, "simulate")

    mod = load_module()
    records = mod.scan_run(run)
    assert records[0]["likely_orphaned"] is True
    assert records[0]["has_matching_log"] is False


def test_with_matching_log_not_orphaned(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    _make_checkpoint(cache, "simulate")

    # Create a matching log file
    logs = run / "logs"
    logs.mkdir(parents=True)
    (logs / "2026-05-17-1200-simulate.log").write_text("ok\n", encoding="utf-8")

    mod = load_module()
    records = mod.scan_run(run)
    assert records[0]["has_matching_log"] is True
    assert records[0]["likely_orphaned"] is False


def test_json_output_is_valid(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    _make_checkpoint(cache, "scan")

    mod = load_module()
    rc = mod.main(["--run", str(run), "--json"])
    assert rc == 1  # orphaned checkpoint found


def test_clear_flag_removes_checkpoint(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    ckpt = _make_checkpoint(cache, "scan")
    assert ckpt.exists()

    mod = load_module()
    rc = mod.main(["--run", str(run), "--clear", "scan"])
    assert rc == 0
    assert not ckpt.exists()


def test_clear_nonexistent_returns_error(tmp_path):
    run = tmp_path / "run"
    run.mkdir()

    mod = load_module()
    rc = mod.main(["--run", str(run), "--clear", "nonexistent"])
    assert rc == 1


def test_format_report_no_records():
    mod = load_module()
    report = mod.format_report([])
    assert "No computation checkpoints found" in report


def test_format_report_with_orphaned(tmp_path):
    run = tmp_path / "run"
    cache = run / "cache"
    _make_checkpoint(cache, "simulate")

    mod = load_module()
    records = mod.scan_run(run)
    report = mod.format_report(records)
    assert "simulate" in report
    assert "orphaned" in report
