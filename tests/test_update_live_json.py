import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update_live_json.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_live_json", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_live_json"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_run(tmp_path):
    run = tmp_path / "runs" / "2026-01-01-test-run"
    run.mkdir(parents=True)
    return run


# ---------------------------------------------------------------------------
# bootstrap_project_json
# ---------------------------------------------------------------------------

def test_bootstrap_creates_json(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    json_path = ulj.bootstrap_project_json(run)
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert "maps" in data
    assert data["maps"][0]["id"] == "live_research_run"


def test_bootstrap_idempotent(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.bootstrap_project_json(run)
    first_ts = json.loads((run / "workflow_map.live.json").read_text())["generated_at"]
    ulj.bootstrap_project_json(run)
    # Second call rewrites with a fresh timestamp; data structure is still valid.
    data = json.loads((run / "workflow_map.live.json").read_text())
    assert data["maps"][0]["id"] == "live_research_run"


# ---------------------------------------------------------------------------
# apply_updates — active step
# ---------------------------------------------------------------------------

def test_active_step_updates_map(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, active_step="Stage 2 running")
    data = json.loads((run / "workflow_map.live.json").read_text())
    assert data["maps"][0]["active_step"] == "Stage 2 running"


# ---------------------------------------------------------------------------
# apply_updates — gate
# ---------------------------------------------------------------------------

def test_gate_creates_node(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Stage 1", status="pass", note="HVG p>=0.38")
    data = json.loads((run / "workflow_map.live.json").read_text())
    nodes = data["maps"][0]["nodes"]
    assert len(nodes) == 1
    node = nodes[0]
    assert node["gate_status"] == "pass"
    assert node["phase"] == "passed"
    assert "HVG" in node["summary"]


def test_gate_upserts_existing_node(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Stage 1", status="pending", note="running")
    ulj.apply_updates(run, gate="Stage 1", status="pass", note="done")
    data = json.loads((run / "workflow_map.live.json").read_text())
    nodes = data["maps"][0]["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["gate_status"] == "pass"


def test_multiple_gates_preserved(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Stage 1", status="pass", note="done")
    ulj.apply_updates(run, gate="Stage 2", status="pending", note="running")
    data = json.loads((run / "workflow_map.live.json").read_text())
    nodes = data["maps"][0]["nodes"]
    assert len(nodes) == 2
    ids = {n["id"] for n in nodes}
    assert "stage_1" in ids
    assert "stage_2" in ids


def test_fail_status_maps_to_blocked_phase(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Stage 3", status="fail", note="broken")
    data = json.loads((run / "workflow_map.live.json").read_text())
    node = data["maps"][0]["nodes"][0]
    assert node["phase"] == "blocked"
    assert node["requires_researcher_review"] is True


# ---------------------------------------------------------------------------
# apply_updates — event packet
# ---------------------------------------------------------------------------

def test_event_packet_creates_node(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    packet = json.dumps({
        "cartographer_update": {
            "node_id": "stage2-synthetic",
            "title": "Stage 2 — Synthetic experiments",
            "status": "passed",
            "node_type": "run",
            "summary": "13 models complete",
            "evidence_strength": "strong",
            "claim_ceiling": "interpretation",
            "review_owner": "professor",
            "result_links": [
                {"path": "outputs/stage2/report.md", "kind": "log", "relation": "documents"},
            ],
        }
    })
    ulj.apply_updates(run, event_json=packet)
    data = json.loads((run / "workflow_map.live.json").read_text())
    nodes = data["maps"][0]["nodes"]
    assert len(nodes) == 1
    node = nodes[0]
    assert node["id"] == "stage2-synthetic"
    assert node["phase"] == "passed"
    assert node["evidence_strength"] == "strong"
    assert node["claim_ceiling"] == "interpretation"
    assert len(node["result_links"]) == 1


def test_event_packet_image_extracted(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    packet = json.dumps({
        "cartographer_update": {
            "node_id": "fig1",
            "title": "Figure 1",
            "status": "passed",
            "result_links": [
                {"path": "outputs/fig1.png", "kind": "figure", "relation": "generated_by"},
            ],
        }
    })
    ulj.apply_updates(run, event_json=packet)
    data = json.loads((run / "workflow_map.live.json").read_text())
    node = data["maps"][0]["nodes"][0]
    assert len(node["images"]) == 1
    assert node["images"][0]["path"] == "outputs/fig1.png"


# ---------------------------------------------------------------------------
# edge auto-linking
# ---------------------------------------------------------------------------

def test_edges_auto_linked(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Gate A", status="pass", note="")
    ulj.apply_updates(run, gate="Gate B", status="pass", note="")
    ulj.apply_updates(run, gate="Gate C", status="pending", note="")
    data = json.loads((run / "workflow_map.live.json").read_text())
    nodes = data["maps"][0]["nodes"]
    # Gate A should edge to Gate B, Gate B to Gate C
    node_a = next(n for n in nodes if "gate_a" in n["id"])
    node_b = next(n for n in nodes if "gate_b" in n["id"])
    assert node_b["id"] in node_a["edges"]
    assert node_b["edges"]  # Gate B edges to Gate C


# ---------------------------------------------------------------------------
# generated_at timestamp updates
# ---------------------------------------------------------------------------

def test_generated_at_updates(tmp_path):
    ulj = load_module()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, active_step="first")
    ts1 = json.loads((run / "workflow_map.live.json").read_text())["generated_at"]
    ulj.apply_updates(run, active_step="second")
    ts2 = json.loads((run / "workflow_map.live.json").read_text())["generated_at"]
    # Both are valid ISO timestamps; second call may produce same second but
    # must always write a valid timestamp.
    assert ts2 >= ts1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_gate_flag(tmp_path, monkeypatch):
    ulj = load_module()
    run = _make_run(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py",
        "--run", str(run),
        "--gate", "Baseline",
        "--status", "pass",
        "--note", "toy model ok",
    ])
    rc = ulj.main()
    assert rc == 0
    data = json.loads((run / "workflow_map.live.json").read_text())
    assert data["maps"][0]["nodes"][0]["gate_status"] == "pass"


def test_cli_missing_status_errors(tmp_path, monkeypatch):
    ulj = load_module()
    run = _make_run(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py",
        "--run", str(run),
        "--gate", "Baseline",
    ])
    rc = ulj.main()
    assert rc != 0


def test_cli_bad_event_json_errors(tmp_path, monkeypatch):
    ulj = load_module()
    run = _make_run(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py",
        "--run", str(run),
        "--event", "{not valid json",
    ])
    rc = ulj.main()
    assert rc != 0


def test_cli_missing_run_errors(tmp_path, monkeypatch):
    ulj = load_module()
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py",
        "--run", str(tmp_path / "nonexistent"),
        "--active-step", "x",
    ])
    rc = ulj.main()
    assert rc != 0
