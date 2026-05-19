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
    assert actions[0]["suggested_command"] == "python scripts/check_orient_recorded.py --project <project-dir>"
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
            "missing_document": 8,
            "needs_researcher_decision": 0,
            "completed": 0,
            "total": 9,
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


def _setup_run_for_write_outputs(tmp_path, monkeypatch, generator):
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
    return run_root, output


def test_write_outputs_refreshes_latest_run_local_dashboard(tmp_path, monkeypatch):
    """Default (central=False): only the run-local dashboard is written."""
    generator = load_generator()
    run_root, output = _setup_run_for_write_outputs(tmp_path, monkeypatch, generator)

    written = generator.write_outputs()

    # Central dashboard is OFF by default — must NOT be in written.
    assert output not in written
    assert not output.exists()
    # Run-local dashboard IS the single source of truth.
    assert run_root / "workflow_map.html" in written
    assert run_root / "workflow_map.live.json" in written
    assert (run_root / "workflow_map.html").exists()
    assert (run_root / "workflow_map.live.json").exists()
    run_data = json.loads((run_root / "workflow_map.live.json").read_text(encoding="utf-8"))
    assert run_data["maps"][0]["id"] == "live_research_run"
    assert "Current Run Dashboard" in (run_root / "workflow_map.html").read_text(encoding="utf-8")


def test_write_outputs_with_central_flag_also_writes_central(tmp_path, monkeypatch):
    """Explicit central=True: both the central and run-local dashboards land."""
    generator = load_generator()
    run_root, output = _setup_run_for_write_outputs(tmp_path, monkeypatch, generator)

    written = generator.write_outputs(central=True)

    assert output in written
    assert output.exists()
    assert run_root / "workflow_map.html" in written


def test_default_build_data_contains_only_live_research_workflow(tmp_path, monkeypatch):
    generator = load_generator()
    _make_live_run(tmp_path, monkeypatch, generator)

    data = generator.build_data()

    assert data["maps"][0]["id"] == "live_research_run"
    assert data["maps"][0]["title"].startswith("Live Research Workflow")
    assert [map_data["id"] for map_data in data["maps"]] == ["live_research_run"]
    assert any(node["phase"] == "blocked" for node in data["maps"][0]["nodes"])
    assert any("convergence_sweep.csv" in item["path"] for node in data["maps"][0]["nodes"] for item in node["responsible"])


def test_static_research_workflow_includes_interview_gate():
    data = json.loads((ROOT / "docs" / "workflow_map.json").read_text(encoding="utf-8"))
    research_map = next(map_data for map_data in data["maps"] if map_data["id"] == "research_workflow")
    nodes = {node["id"]: node for node in research_map["nodes"]}

    assert nodes["orient_gate"]["edges"] == ["interview_gate"]
    assert nodes["interview_gate"]["title"] == "3. Interview Gate"
    assert nodes["interview_gate"]["edges"] == ["literature_gate"]
    assert any(
        item["path"] == "scripts/check_interview_recorded.py"
        for item in nodes["interview_gate"]["responsible"]
    )


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
    assert "beta-badge" in html
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


def test_workflow_map_template_includes_persistent_dark_mode_toggle():
    generator = load_generator()

    html = generator.build_html(generator.build_data())

    assert 'data-theme' in html
    assert 'workflowMapTheme' in html
    assert 'id="themeToggle"' in html
    assert ':root[data-theme="dark"]' in html
    assert 'aria-label' in html


def test_embedded_workflow_data_remains_valid_json():
    generator = load_generator()

    html = generator.build_html(generator.build_data())
    match = re.search(r"(?:const|let) DATA = (?P<data>.*?);\n", html, re.DOTALL)

    assert match is not None
    embedded = json.loads(match.group("data"))
    assert all(action["linked_document"]["label"] for action in embedded["maps"][0]["dashboard"]["actions"])
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


LITERATURE_WORKFLOW_FIXTURE = """\
# Live Workflow

## Active Step

- Current step: Literature review in progress

## Gate Status

| Gate | Status | Note |
|---|---|---|
| Literature review and replanning | pass | Review complete |

## Evidence Links

- `docs/literature/literature_review_plan.md`

## Next Review Checkpoint

- Researcher decision needed: approve replanning memo
"""


def _make_literature_run(tmp_path, monkeypatch, generator):
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-19-literature-run" / "docs"
    run_docs.mkdir(parents=True)
    (run_docs / "live_workflow_diagram.md").write_text(LITERATURE_WORKFLOW_FIXTURE, encoding="utf-8")
    lit_dir = run_docs / "literature"
    lit_dir.mkdir()
    (lit_dir / "literature_review_plan.md").write_text(
        "# Literature Review Plan\n\n## Literature Gate Status\n\nStatus: ready\n",
        encoding="utf-8",
    )
    (lit_dir / "paper_request_queue.md").write_text(
        "# Paper Request Queue\n\n"
        "| Paper ID | Citation | Status |\n"
        "|---|---|---|\n"
        "| P1 | Smith 2020 | reviewed |\n"
        "| P2 | Jones 2021 | open |\n"
        "| P3 | Lee 2022 | reviewed |\n",
        encoding="utf-8",
    )
    (lit_dir / "replanning_memo.md").write_text(
        "# Replanning Memo\n\nDecision: proceed with current model spec.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)


def test_literature_gate_node_has_result_summary_and_links(tmp_path, monkeypatch):
    generator = load_generator()
    _make_literature_run(tmp_path, monkeypatch, generator)

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}
    node = nodes["literature_review_and_replanning"]

    # result_summary is populated from the plan and queue files
    assert node["result_summary"]["gate_status"] == "ready"
    assert node["result_summary"]["papers_total"] == "3"
    assert node["result_summary"]["papers_open_requests"] == "1"

    # gate-specific interpretation links are prepended before evidence links
    link_paths = " ".join(item["path"] for item in node["interpretation_links"])
    assert "literature_review_plan" in link_paths
    assert "paper_request_queue" in link_paths
    assert "replanning_memo" in link_paths


def test_literature_gate_result_summary_without_files(tmp_path, monkeypatch):
    """When the literature files are absent the builder returns 'not recorded' and
    gate_specific_links returns no dead links."""
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-19-no-lit-files" / "docs"
    run_docs.mkdir(parents=True)
    (run_docs / "live_workflow_diagram.md").write_text(LITERATURE_WORKFLOW_FIXTURE, encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}
    node = nodes["literature_review_and_replanning"]

    assert node["result_summary"]["gate_status"] == "not recorded"
    assert node["result_summary"]["papers_total"] == "not recorded"
    assert node["result_summary"]["papers_open_requests"] == "not recorded"
    # gate_specific_links returns nothing when files are missing — avoids dead links
    run_root = runs_root / "2026-05-19-no-lit-files"
    specific = generator.gate_specific_links("literature_review_and_replanning", run_root)
    assert specific == []


def test_literature_summary_appears_in_dashboard_recommended_review(tmp_path, monkeypatch):
    """literature/summary.md and literature/reviews/ are both listed under Recommended Review."""
    generator = load_generator()
    _make_literature_run(tmp_path, monkeypatch, generator)

    map_data = generator.build_data()["maps"][0]
    rec = next(g for g in map_data["dashboard"]["document_groups"] if g["id"] == "recommended_review")
    labels = [doc["label"] for doc in rec["documents"]]

    assert "Literature Summary" in labels
    assert "Literature Reviews" in labels


MERMAID_WORKFLOW_FIXTURE = """\
# Live Workflow

## Active Step

- Current step: Literature review

## Workflow Diagram

```mermaid
flowchart LR
    I["Interview gate"] --> L["Literature review and replanning"]
    L --> I
    L --> S["Test design seed"]
```

## Gate Status

| Gate | Status | Note |
|---|---|---|
| Interview gate | pass | Interview complete |
| Literature review and replanning | pass | Review done, replanning triggered |
| Test design seed | pending | Awaiting seed |

## Evidence Links

- `docs/gates/interview_notes.md`

## Next Review Checkpoint

- Researcher decision needed: begin seed design
"""


def test_mermaid_edges_create_replanning_back_edge(tmp_path, monkeypatch):
    """Mermaid workflow diagram edges override sequential chaining.

    The literature gate's L --> I back-edge must appear in the node's 'edges' list,
    along with the forward edge L --> S.  The interview gate must point forward to
    the literature gate (not sequentially to seed).
    """
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-19-mermaid-run" / "docs"
    run_docs.mkdir(parents=True)
    (run_docs / "live_workflow_diagram.md").write_text(MERMAID_WORKFLOW_FIXTURE, encoding="utf-8")
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}

    # Forward edge: interview → literature
    assert "literature_review_and_replanning" in nodes["interview_gate"]["edges"]
    # Back-edge (replanning loop): literature → interview
    assert "interview_gate" in nodes["literature_review_and_replanning"]["edges"]
    # Forward edge: literature → seed
    assert "test_design_seed" in nodes["literature_review_and_replanning"]["edges"]


def test_literature_summary_action_guidance_is_recorded():
    """The action queue provides a meaningful why and command for Literature Summary."""
    generator = load_generator()

    guidance = generator.ACTION_GUIDANCE.get("Literature Summary", {})

    assert "compile_literature_summary" in guidance.get("suggested_command", "")
    assert guidance.get("why")


def test_mermaid_threshold_requires_ceil_half_nodes(tmp_path, monkeypatch):
    """With 3 gate nodes, 1 Mermaid match is below the ceiling-half threshold (2);
    sequential chaining must be used instead."""
    generator = load_generator()
    runs_root = tmp_path / "ResearchPartner-runs"
    run_docs = runs_root / "2026-05-19-threshold-run" / "docs"
    run_docs.mkdir(parents=True)
    # Only the first gate appears in the Mermaid diagram; the other two don't.
    (run_docs / "live_workflow_diagram.md").write_text(
        "# Live Workflow\n\n"
        "## Active Step\n\n- Current step: Test\n\n"
        "## Workflow Diagram\n\n"
        "```mermaid\n"
        "flowchart LR\n"
        '    A["Baseline"] --> X["Nonexistent gate"]\n'
        "```\n\n"
        "## Gate Status\n\n"
        "| Gate | Status | Note |\n"
        "|---|---|---|\n"
        "| Baseline | pass | Done |\n"
        "| Refinement trend | pass | Done |\n"
        "| Fixed ratio convergence | pending |  |\n\n"
        "## Evidence Links\n\n"
        "## Next Review Checkpoint\n\n- None\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generator, "RUNS_ROOT", runs_root)

    nodes = {node["id"]: node for node in generator.build_data()["maps"][0]["nodes"]}

    # Sequential chaining should apply: baseline → refinement_trend → fixed_ratio
    assert nodes["baseline"]["edges"] == ["refinement_trend"]
    assert nodes["refinement_trend"]["edges"] == ["fixed_ratio_convergence"]


def test_gate_specific_links_for_orient_and_interview(tmp_path):
    """orient_gate and interview_gate return links to their source documents."""
    generator = load_generator()
    run_root = tmp_path / "run"
    gates_dir = run_root / "docs" / "gates"
    gates_dir.mkdir(parents=True)
    (gates_dir / "orient_note.md").write_text("# Orient\n", encoding="utf-8")
    (gates_dir / "interview_notes.md").write_text("# Interview\n", encoding="utf-8")

    orient_links = generator.gate_specific_links("orient_gate", run_root)
    interview_links = generator.gate_specific_links("interview_gate", run_root)

    assert any("orient_note" in item["path"] for item in orient_links)
    assert any("interview_notes" in item["path"] for item in interview_links)


def test_gate_specific_links_for_baseline_and_claim(tmp_path):
    """baseline and claim_gate return links to their source documents."""
    generator = load_generator()
    run_root = tmp_path / "run"
    (run_root / "docs" / "gates").mkdir(parents=True)
    (run_root / "docs" / "plan").mkdir(parents=True)
    (run_root / "docs" / "process").mkdir(parents=True)
    (run_root / "docs" / "gates" / "baseline_registry.md").write_text("# Registry\n", encoding="utf-8")
    (run_root / "docs" / "plan" / "baseline_strategy.md").write_text("# Strategy\n", encoding="utf-8")
    (run_root / "docs" / "gates" / "validation_log.md").write_text("# Log\n", encoding="utf-8")

    baseline_links = generator.gate_specific_links("baseline", run_root)
    claim_links = generator.gate_specific_links("claim_gate", run_root)

    assert any("baseline_registry" in item["path"] for item in baseline_links)
    assert any("baseline_strategy" in item["path"] for item in baseline_links)
    assert any("validation_log" in item["path"] for item in claim_links)
