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


def test_live_workflow_diagram_agent_scenario_is_evaluated():
    evaluator = load_evaluator()

    names = [scenario.name for scenario in evaluator.SCENARIOS]

    assert "live_workflow_diagram_agent" in names


def test_harness_evaluator_has_eight_scenarios():
    evaluator = load_evaluator()

    assert len(evaluator.SCENARIOS) == 8
