"""Unit tests for lineage-specific behavior added to update_live_json.py.

Covers:
  - find_broken_edges(): broken graph_links.to and dangling edges
  - anomaly resolution lifecycle: resolved status flips limits → superseded
  - --validate CLI flag: returns 2 on broken edges, 0 on clean
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "update_live_json", ROOT / "scripts" / "update_live_json.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_live_json"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_run(tmp_path):
    run = tmp_path / "runs" / "2026-01-01-test"
    run.mkdir(parents=True)
    return run


# ---------------------------------------------------------------------------
# Broken-edge linter
# ---------------------------------------------------------------------------

def test_find_broken_edges_clean(tmp_path):
    ulj = load()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "a", "title": "A", "node_type": "decision",
    }}))
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "b", "title": "B", "node_type": "decision",
        "graph_links": [{"from": "b", "to": "a", "relation": "depends_on"}],
    }}))
    assert ulj.find_broken_edges(run) == []


def test_find_broken_edges_catches_typo(tmp_path):
    ulj = load()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "claim_x", "title": "X", "node_type": "claim", "lineage_kind": "claim",
        "graph_links": [{"from": "claim_x", "to": "result_typo", "relation": "supports"}],
    }}))
    broken = ulj.find_broken_edges(run)
    # Both `edges` (auto-relinked) and `graph_links.to` should fire.
    assert any(b["field"] == "graph_links.to" and b["target"] == "result_typo" for b in broken)


def test_find_broken_edges_missing_json(tmp_path):
    ulj = load()
    run = _make_run(tmp_path)
    # No apply_updates → no JSON file → returns empty list, doesn't raise.
    assert ulj.find_broken_edges(run) == []


# ---------------------------------------------------------------------------
# Anomaly resolution flips limits edge → superseded
# ---------------------------------------------------------------------------

def test_anomaly_resolution_flips_limits_edge(tmp_path):
    ulj = load()
    run = _make_run(tmp_path)
    # Seed the target node first.
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "claim_x", "title": "X",
        "node_type": "claim", "lineage_kind": "claim",
    }}))
    # Active anomaly with a fresh limits edge.
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "anom_z", "title": "Z",
        "node_type": "anomaly", "lineage_kind": "anomaly", "status": "blocked",
        "graph_links": [{"from": "anom_z", "to": "claim_x", "relation": "limits", "status": "fresh"}],
    }}))
    # Re-emit with status=resolved.
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "anom_z", "title": "Z",
        "node_type": "anomaly", "lineage_kind": "anomaly", "status": "resolved",
        "graph_links": [{"from": "anom_z", "to": "claim_x", "relation": "limits", "status": "fresh"}],
    }}))
    data = json.loads((run / "workflow_map.live.json").read_text(encoding="utf-8"))
    anom = next(n for n in data["maps"][0]["nodes"] if n["id"] == "anom_z")
    assert anom["graph_links"][0]["status"] == "superseded"


def test_active_anomaly_keeps_limits_fresh(tmp_path):
    ulj = load()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "claim_x", "title": "X", "node_type": "claim", "lineage_kind": "claim",
    }}))
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "anom_a", "title": "Active",
        "node_type": "anomaly", "lineage_kind": "anomaly", "status": "blocked",
        "graph_links": [{"from": "anom_a", "to": "claim_x", "relation": "limits", "status": "fresh"}],
    }}))
    data = json.loads((run / "workflow_map.live.json").read_text(encoding="utf-8"))
    anom = next(n for n in data["maps"][0]["nodes"] if n["id"] == "anom_a")
    assert anom["graph_links"][0]["status"] == "fresh"


# ---------------------------------------------------------------------------
# --validate CLI flag
# ---------------------------------------------------------------------------

def test_cli_validate_clean_returns_zero(tmp_path, monkeypatch):
    ulj = load()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, gate="Stage 1", status="pass", note="ok")
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py", "--run", str(run), "--validate",
    ])
    rc = ulj.main()
    assert rc == 0


def test_cli_validate_broken_returns_two(tmp_path, monkeypatch):
    ulj = load()
    run = _make_run(tmp_path)
    ulj.apply_updates(run, event_json=json.dumps({"cartographer_update": {
        "node_id": "claim_x", "title": "X", "node_type": "claim", "lineage_kind": "claim",
        "graph_links": [{"from": "claim_x", "to": "ghost", "relation": "supports"}],
    }}))
    monkeypatch.setattr(sys, "argv", [
        "update_live_json.py", "--run", str(run), "--validate",
    ])
    rc = ulj.main()
    assert rc == 2
