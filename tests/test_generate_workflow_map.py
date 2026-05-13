import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_workflow_map.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_workflow_map", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["generate_workflow_map"] = module
    spec.loader.exec_module(module)
    return module


def test_default_build_data_contains_only_live_research_workflow():
    generator = load_generator()

    data = generator.build_data()

    assert data["maps"][0]["id"] == "live_research_run"
    assert data["maps"][0]["title"].startswith("Live Research Workflow")
    assert [map_data["id"] for map_data in data["maps"]] == ["live_research_run"]
    assert any(node["phase"] == "blocked" for node in data["maps"][0]["nodes"])
    assert any("convergence_sweep.csv" in item["path"] for node in data["maps"][0]["nodes"] for item in node["responsible"])


def test_live_nodes_include_result_summaries_and_images():
    generator = load_generator()

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}

    assert "final_relative_error" in nodes["baseline"]["result_summary"]
    assert any(image["path"].endswith("amplitude_decay.png") for image in nodes["baseline"]["images"])
    assert "observed_order" in nodes["fixed_ratio_convergence"]["result_summary"]
    assert any(
        image["path"].endswith("fixed_ratio_convergence.png")
        for image in nodes["fixed_ratio_convergence"]["images"]
    )
    assert "max_relative_error" in nodes["multi_mode_validation"]["result_summary"]
    assert any(
        image["path"].endswith("multimode_amplitude_decay.png")
        for image in nodes["multi_mode_validation"]["images"]
    )
    assert "minimum_value" in nodes["positivity_sanity"]["result_summary"]
    assert any(
        image["path"].endswith("positivity_profile.png")
        for image in nodes["positivity_sanity"]["images"]
    )
    assert "stability_ratio" in nodes["anomaly_probe"]["result_summary"]


def test_paper_logic_is_only_added_when_requested():
    generator = load_generator()

    data = generator.build_data(include_paper_logic=True)

    assert [map_data["id"] for map_data in data["maps"]] == [
        "live_research_run",
        "paper_logic",
    ]


def test_live_map_html_mentions_process_tracking_not_claim_evidence():
    generator = load_generator()

    html = generator.build_html(generator.build_data())

    assert "process-tracking" in html
    assert "must not strengthen scientific claims" in html
    assert "Live Research Workflow" in html
    assert "Physics Research Workflow" not in html
    assert "Paper Logic Structure" not in html
    assert "Auto-refreshes every 10 seconds" in html
    assert "Result Summary" in html
    assert "Evidence Images" in html
    assert "<img" in html
