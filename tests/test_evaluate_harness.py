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


def test_harness_evaluator_has_twelve_scenarios():
    evaluator = load_evaluator()

    assert len(evaluator.SCENARIOS) == 12


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
