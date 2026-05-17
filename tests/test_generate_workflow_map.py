import importlib.util
import json
import os
import re
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


LIVE_WORKFLOW_FIXTURE = """\
# Live Workflow

## Active Step

- Current step: Running validation experiments

## Gate Status

| Gate | Status | Note |
|---|---|---|
| Baseline | pass | Toy baseline validated |
| Refinement trend | pass | Convergence trend established |
| Fixed ratio convergence | pass | Order confirmed |
| Multi mode validation | fail | Multi-mode tests failing |
| Positivity sanity | pass | Positivity confirmed |
| Dirichlet boundary | pass | Boundary conditions met |
| Anomaly probe | pass | No anomalies detected |
| Claim gate | pass | Claims scoped |

## Evidence Links

- `docs/convergence_sweep.csv`

## Next Review Checkpoint

- Researcher decision needed: review multi-mode failure
"""


def _make_live_run(tmp_path, monkeypatch, generator):
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-15-fixture-run" / "docs"
    run_docs.mkdir(parents=True)
    (run_docs / "live_workflow_diagram.md").write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)


def test_latest_live_workflow_path_reads_current_scaffold_layout(tmp_path, monkeypatch):
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-17-current-layout" / "docs" / "process"
    run_docs.mkdir(parents=True)
    live_path = run_docs / "live_workflow_diagram.md"
    live_path.write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    assert generator.latest_live_workflow_path() == live_path
    assert generator.build_data()["maps"][0]["id"] == "live_research_run"


def test_live_map_uses_run_root_for_current_process_layout(tmp_path, monkeypatch):
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_root = runs_root / "2026-05-17-current-layout"
    process_docs = run_root / "docs" / "process"
    process_docs.mkdir(parents=True)
    live_path = process_docs / "live_workflow_diagram.md"
    live_path.write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    (run_root / "docs" / "gates").mkdir(parents=True)
    (run_root / "docs" / "gates" / "orient_note.md").write_text("# Orient\n", encoding="utf-8")
    (run_root / "docs" / "plan").mkdir(parents=True)
    (run_root / "docs" / "plan" / "research_plan.md").write_text("# Plan\n", encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)
    monkeypatch.setattr(generator, "OUTPUT", tmp_path / "harness" / "docs" / "workflow_map.html")

    map_data = generator.build_data()["maps"][0]

    assert map_data["title"] == "Live Research Workflow: 2026-05-17-current-layout"
    assert any(
        item["path"].endswith("2026-05-17-current-layout/docs/convergence_sweep.csv")
        for node in map_data["nodes"]
        for item in node["responsible"]
    )
    assert map_data["dashboard"]["title"] == "Current Run Dashboard"
    assert map_data["dashboard"]["document_groups"][0]["id"] == "needs_input"
    assert any(
        doc["path"].endswith("2026-05-17-current-layout/docs/gates/orient_note.md")
        for group in map_data["dashboard"]["document_groups"]
        for doc in group["documents"]
    )
    actions = map_data["dashboard"]["actions"]
    assert actions[0]["category"] == "Needs Input"
    assert actions[0]["title"] == "Review Orient Note"
    assert actions[0]["status"] == "Needs researcher decision"
    assert actions[0]["linked_document"]["label"] == "Orient Note"
    assert actions[0]["linked_document"]["status"] == "Needs researcher decision"
    assert actions[0]["suggested_command"] == "python scripts/check_orient_recorded.py --run <run-dir>"
    assert actions[0]["why"] == "Confirm the run has a recorded task classification and first researcher-facing question."
    assert {
        action["linked_document"]["label"]: action["status"]
        for action in actions
        if action["linked_document"]["label"] in {"Meeting Notes", "Live Workflow Diagram"}
    } == {
        "Meeting Notes": "Missing document",
        "Live Workflow Diagram": "Ready to review",
    }
    summary = map_data["dashboard"]["summary"]
    assert summary == {
        "needs_input": {
            "ready_to_review": 0,
            "missing_document": 4,
            "needs_researcher_decision": 1,
            "completed": 0,
            "total": 5,
        },
        "needs_approval": {
            "ready_to_review": 0,
            "missing_document": 4,
            "needs_researcher_decision": 1,
            "completed": 0,
            "total": 5,
        },
        "recommended_review": {
            "ready_to_review": 1,
            "missing_document": 6,
            "needs_researcher_decision": 0,
            "completed": 0,
            "total": 7,
        },
    }


def test_latest_live_workflow_path_prefers_newest_current_or_legacy_layout(tmp_path, monkeypatch):
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    legacy_docs = runs_root / "2026-05-16-legacy-layout" / "docs"
    current_docs = runs_root / "2026-05-17-current-layout" / "docs" / "process"
    legacy_docs.mkdir(parents=True)
    current_docs.mkdir(parents=True)
    legacy_path = legacy_docs / "live_workflow_diagram.md"
    current_path = current_docs / "live_workflow_diagram.md"
    legacy_path.write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    current_path.write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    os.utime(legacy_path, (1_700_000_000, 1_700_000_000))
    os.utime(current_path, (1_800_000_000, 1_800_000_000))
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    assert generator.latest_live_workflow_path() == current_path


def test_write_outputs_refreshes_latest_run_local_dashboard(tmp_path, monkeypatch):
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_root = runs_root / "2026-05-17-current-layout"
    process_docs = run_root / "docs" / "process"
    process_docs.mkdir(parents=True)
    (process_docs / "live_workflow_diagram.md").write_text(LIVE_WORKFLOW_FIXTURE, encoding="utf-8")
    source = tmp_path / "harness" / "docs" / "workflow_map.json"
    output = tmp_path / "harness" / "docs" / "workflow_map.html"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"maps": []}), encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)
    monkeypatch.setattr(generator, "SOURCE", source)
    monkeypatch.setattr(generator, "OUTPUT", output)

    written = generator.write_outputs()

    assert output in written
    assert run_root / "workflow_map.html" in written
    assert run_root / "workflow_map.live.json" in written
    assert (run_root / "workflow_map.html").exists()
    assert (run_root / "workflow_map.live.json").exists()
    run_data = json.loads((run_root / "workflow_map.live.json").read_text(encoding="utf-8"))
    assert run_data["maps"][0]["id"] == "live_research_run"
    assert "Current Run Dashboard" in (run_root / "workflow_map.html").read_text(encoding="utf-8")


def test_default_build_data_contains_only_live_research_workflow(tmp_path, monkeypatch):
    generator = load_generator()
    _make_live_run(tmp_path, monkeypatch, generator)

    data = generator.build_data()

    assert data["maps"][0]["id"] == "live_research_run"
    assert data["maps"][0]["title"].startswith("Live Research Workflow")
    assert [map_data["id"] for map_data in data["maps"]] == ["live_research_run"]
    assert any(node["phase"] == "blocked" for node in data["maps"][0]["nodes"])
    assert any("convergence_sweep.csv" in item["path"] for node in data["maps"][0]["nodes"] for item in node["responsible"])


def test_live_nodes_include_result_summaries_and_images(tmp_path, monkeypatch):
    generator = load_generator()
    _make_live_run(tmp_path, monkeypatch, generator)

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
    assert "Action Queue" in html
    assert "Suggested Next Command" in html
    assert "data-action" in html
    assert "renderActionQueue" in html
    assert "Dashboard Summary" in html
    assert html.index("<h2>Dashboard Summary</h2>") < html.index("<h2>Action Queue</h2>")
    assert "action-group" in html
    assert "Next action: Review" in html
    assert "Select an action" in html
    assert ".slice(0, 4)" not in html
    assert "let activeAction = null" in html
    assert "renderDashboard(map)" not in html


def test_embedded_workflow_data_remains_valid_json():
    generator = load_generator()

    html = generator.build_html(generator.build_data())
    match = re.search(r"(?:const|let) DATA = (?P<data>.*?);\n", html, re.DOTALL)

    assert match is not None
    embedded = json.loads(match.group("data"))
    assert embedded["maps"][0]["dashboard"]["actions"][0]["linked_document"]["label"] == "Orient Note"
    statuses = {
        action["status"]
        for action in embedded["maps"][0]["dashboard"]["actions"]
    }
    assert "available" not in statuses
    assert "missing" not in statuses


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
