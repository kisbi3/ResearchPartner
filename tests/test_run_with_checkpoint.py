import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".harness" / "scripts"))

from run_with_checkpoint import CheckpointManager  # noqa: E402


def test_load_returns_none_when_no_checkpoint(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    assert ckpt.load() is None


def test_save_creates_checkpoint_file(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    ckpt.save({"step": 1, "value": 42})
    assert (tmp_path / "checkpoint_sim.pkl").exists()


def test_load_returns_saved_state(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    ckpt.save({"step": 5, "results": [1, 2, 3]})

    ckpt2 = CheckpointManager(tmp_path, "sim")
    state = ckpt2.load()
    assert state is not None
    assert state["step"] == 5
    assert state["results"] == [1, 2, 3]


def test_clear_removes_checkpoint(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    ckpt.save({"step": 1})
    assert (tmp_path / "checkpoint_sim.pkl").exists()
    ckpt.clear()
    assert not (tmp_path / "checkpoint_sim.pkl").exists()


def test_clear_on_missing_file_is_silent(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    ckpt.clear()  # should not raise


def test_maybe_save_respects_interval(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim", interval=3)
    ckpt_path = tmp_path / "checkpoint_sim.pkl"

    ckpt.maybe_save({"step": 1})  # count=1, no save
    assert not ckpt_path.exists()

    ckpt.maybe_save({"step": 2})  # count=2, no save
    assert not ckpt_path.exists()

    ckpt.maybe_save({"step": 3})  # count=3, save
    assert ckpt_path.exists()


def test_atomic_write_leaves_no_tmp(tmp_path):
    ckpt = CheckpointManager(tmp_path, "sim")
    ckpt.save({"step": 1})
    tmp_file = tmp_path / "checkpoint_sim.tmp"
    assert not tmp_file.exists()


def test_corrupted_checkpoint_returns_none(tmp_path, capsys):
    ckpt_path = tmp_path / "checkpoint_sim.pkl"
    ckpt_path.write_bytes(b"not valid pickle data!!!!")
    ckpt = CheckpointManager(tmp_path, "sim")
    state = ckpt.load()
    assert state is None
    captured = capsys.readouterr()
    assert "WARNING" in captured.err


def test_stem_isolated_per_script(tmp_path):
    ckpt_a = CheckpointManager(tmp_path, "scan")
    ckpt_b = CheckpointManager(tmp_path, "fit")
    ckpt_a.save({"x": 10})
    ckpt_b.save({"x": 20})

    state_a = CheckpointManager(tmp_path, "scan").load()
    state_b = CheckpointManager(tmp_path, "fit").load()
    assert state_a["x"] == 10
    assert state_b["x"] == 20
