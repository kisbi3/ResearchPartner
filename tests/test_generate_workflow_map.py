import importlib.util
import json
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
    assert "final_relative_error" in nodes["dirichlet_boundary"]["result_summary"]
    assert any(
        image["path"].endswith("dirichlet_amplitude_decay.png")
        for image in nodes["dirichlet_boundary"]["images"]
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


def test_cartographer_update_events_create_linked_research_graph(tmp_path, monkeypatch):
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-14-linked-graph" / "docs"
    run_docs.mkdir(parents=True)
    update = {
        "cartographer_update": {
            "from": "coding-subagent",
            "event_type": "figure",
            "node_id": "dispersion-figure-run-014",
            "title": "Dispersion Figure Run 014",
            "node_type": "figure",
            "summary": "Generated dispersion relation figure for toy baseline.",
            "status": "pending_review",
            "link_status": "fresh",
            "evidence_strength": "moderate",
            "claim_ceiling": "observation",
            "review_owner": "researcher",
            "requires_researcher_review": True,
            "code_links": [
                {
                    "path": "scripts/plot_dispersion.py",
                    "line": 18,
                    "role": "renders dispersion figure",
                    "relation": "generates_figure",
                    "status": "fresh",
                }
            ],
            "result_links": [
                {
                    "path": "outputs/run_014/dispersion.png",
                    "kind": "figure",
                    "relation": "generated_by",
                    "status": "fresh",
                    "preview": "thumbnail",
                }
            ],
            "interpretation_links": [
                {
                    "path": "docs/validation_log.md",
                    "anchor": "run-014",
                    "relation": "documents_uncertainty",
                    "status": "pending_review",
                }
            ],
            "graph_links": [
                {
                    "from": "toy-baseline-run-014",
                    "to": "dispersion-figure-run-014",
                    "relation": "generated_by",
                    "status": "fresh",
                }
            ],
        }
    }
    (run_docs / "live_workflow_diagram.md").write_text(
        "# Live Workflow\n\n"
        "## Active Step\n\n- Current step: Evaluate\n\n"
        "## Gate Status\n\n"
        "| Gate | Status | Note |\n"
        "|---|---|---|\n"
        "| Toy baseline | pass | Ready for figure review |\n\n"
        "## Cartographer Update Events\n\n"
        "```json\n"
        + json.dumps(update)
        + "\n```\n\n"
        "## Evidence Links\n\n- `docs/validation_log.md`\n\n"
        "## Next Review Checkpoint\n\n- Researcher decision needed: inspect figure\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}
    node = nodes["dispersion-figure-run-014"]

    assert node["node_type"] == "figure"
    assert node["link_status"] == "fresh"
    assert node["evidence_strength"] == "moderate"
    assert node["claim_ceiling"] == "observation"
    assert node["review_owner"] == "researcher"
    assert node["requires_researcher_review"] is True
    assert node["code_links"][0]["line"] == 18
    assert node["result_links"][0]["preview"] == "thumbnail"
    assert node["interpretation_links"][0]["anchor"] == "run-014"
    assert node["graph_links"][0]["relation"] == "generated_by"

    html = generator.build_html(generator.build_data())
    assert "Code Links" in html
    assert "Result Links" in html
    assert "Interpretation Links" in html
    assert "Evidence Strength" in html
    assert "Claim Ceiling" in html
