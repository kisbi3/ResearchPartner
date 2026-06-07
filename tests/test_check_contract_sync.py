import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "check_contract_sync.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_contract_sync", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_contract_sync"] = module
    spec.loader.exec_module(module)
    return module


def test_agents_and_gemini_are_byte_identical():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    gemini = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
    assert agents == gemini, "AGENTS.md and GEMINI.md must be byte-identical"


def test_checker_returns_zero_when_synced():
    checker = load_checker()
    assert checker.main() == 0


def test_agents_and_gemini_stay_under_word_budget():
    checker = load_checker()

    for filename in ("AGENTS.md", "GEMINI.md"):
        path = ROOT / filename
        assert checker.word_count(path.read_text(encoding="utf-8")) <= checker.MAX_CONTRACT_WORDS


def test_checker_detects_drift(tmp_path, monkeypatch):
    checker = load_checker()

    left = tmp_path / "A.md"
    right = tmp_path / "B.md"
    left.write_text("alpha\n", encoding="utf-8")
    right.write_text("beta\n", encoding="utf-8")

    errors = checker.compare_pair(left, right)
    assert errors
    assert "alpha" in errors[0] or "beta" in errors[0]


def test_checker_reports_missing_file(tmp_path):
    checker = load_checker()
    left = tmp_path / "exists.md"
    left.write_text("x\n", encoding="utf-8")
    right = tmp_path / "missing.md"

    errors = checker.compare_pair(left, right)
    assert errors
    assert "missing.md" in errors[0]


def test_checker_detects_oversized_contract_file(tmp_path):
    checker = load_checker()
    oversized = tmp_path / "oversized.md"
    oversized.write_text("word " * (checker.MAX_CONTRACT_WORDS + 1), encoding="utf-8")

    errors = checker.check_word_budget(oversized)

    assert errors
    assert "word budget" in errors[0]
