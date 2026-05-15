import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_baseline_gate.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_baseline_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_baseline_gate"] = module
    spec.loader.exec_module(module)
    return module


def make_run(tmp_path: Path, registry_body: str | None, live_body: str | None = None) -> Path:
    run = tmp_path / "run"
    docs = run / "docs"
    docs.mkdir(parents=True)
    if registry_body is not None:
        (docs / "baseline_registry.md").write_text(registry_body, encoding="utf-8")
    if live_body is not None:
        (docs / "live_workflow_diagram.md").write_text(live_body, encoding="utf-8")
    return run


REGISTRY_HEADER = (
    "# Baseline Registry\n\n"
    "| ID | Date | Target | Type | Validates | Expected Behavior | Status | Linked Log |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def test_missing_registry_fails(tmp_path):
    checker = load_checker()
    run = tmp_path / "run"
    (run / "docs").mkdir(parents=True)
    code, _ = checker.check_run(run)
    assert code == 1


def test_template_only_registry_fails(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | YYYY-MM-DD |  | toy |  |  | planned/pass/fail/partial/waived |  |\n"
    )
    run = make_run(tmp_path, body)
    code, _ = checker.check_run(run)
    assert code == 1


def test_pass_entry_satisfies_gate(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy | period |  | pass | log.md |\n"
    )
    run = make_run(tmp_path, body)
    code, messages = checker.check_run(run)
    assert code == 0
    assert "pass" in messages[0].lower()


def test_planned_entry_does_not_satisfy_gate(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy |  |  | planned |  |\n"
    )
    run = make_run(tmp_path, body)
    code, _ = checker.check_run(run)
    assert code == 1


def test_waiver_without_claim_ceiling_demotion_fails(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy |  |  | waived |  |\n"
    )
    run = make_run(tmp_path, body, live_body="# Live\n")
    code, messages = checker.check_run(run)
    assert code == 1
    assert "claim ceiling" in messages[0].lower()


def test_waiver_with_claim_ceiling_observation_passes(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy |  |  | waived |  |\n"
    )
    live = "# Live\n\n- Claim ceiling: observation\n"
    run = make_run(tmp_path, body, live_body=live)
    code, _ = checker.check_run(run)
    assert code == 0


def test_waiver_missing_live_workflow_fails(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy |  |  | waived |  |\n"
    )
    run = make_run(tmp_path, body)
    code, _ = checker.check_run(run)
    assert code == 1


def test_run_level_default_registry_fails(tmp_path):
    """The run-level baseline_registry.md created by start_research_run.py has
    no table and should fail until the researcher adds at least one entry."""
    checker = load_checker()
    body = "# Baseline Registry\n\n- Run-specific baseline target:\n"
    run = make_run(tmp_path, body)
    code, _ = checker.check_run(run)
    assert code == 1


def test_main_cli_pass(tmp_path):
    checker = load_checker()
    body = (
        REGISTRY_HEADER
        + "| B-001 | 2026-05-15 | sho | toy |  |  | pass |  |\n"
    )
    run = make_run(tmp_path, body)
    assert checker.main(["--run", str(run)]) == 0


def test_main_cli_fail(tmp_path):
    checker = load_checker()
    run = tmp_path / "run"
    (run / "docs").mkdir(parents=True)
    assert checker.main(["--run", str(run)]) == 1
