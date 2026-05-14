import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_harness.py"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("evaluate_harness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["evaluate_harness"] = module
    spec.loader.exec_module(module)
    return module


def test_multi_agent_orchestration_scenarios_are_evaluated():
    evaluator = load_evaluator()

    names = [scenario.name for scenario in evaluator.SCENARIOS]

    assert "live_workflow_diagram_agent" in names
    assert "professor_orchestration" in names
    assert "graduate_test_design_agents" in names
    assert "coding_subagent_claim_discipline" in names
    assert "completion_conference_reporting" in names


def test_harness_evaluator_includes_hook_scenarios():
    evaluator = load_evaluator()

    assert len(evaluator.SCENARIOS) == 15


def test_orchestration_scenarios_require_run_templates():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert (
        "docs/run_templates/live_workflow_diagram_template.md"
        in scenarios["live_workflow_diagram_agent"].docs
    )
    assert (
        "docs/run_templates/research_run_packet_template.md"
        in scenarios["completion_conference_reporting"].docs
    )
    assert (
        "scripts/start_research_run.py"
        in scenarios["live_workflow_diagram_agent"].rule_terms
    )


def test_scientific_loop_hook_scenarios_are_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "hook_aware_scientific_loop" in scenarios
    assert "provenance_and_reproducibility_hooks" in scenarios
    assert "manuscript_and_artifact_drift_hooks" in scenarios
    assert "Task Intake Hook" in scenarios["hook_aware_scientific_loop"].rule_terms
    assert "Baseline Gate Hook" in scenarios["hook_aware_scientific_loop"].rule_terms
    assert (
        "Figure Provenance Hook"
        in scenarios["provenance_and_reproducibility_hooks"].rule_terms
    )
    assert (
        "Artifact Freshness Hook"
        in scenarios["manuscript_and_artifact_drift_hooks"].rule_terms
    )
