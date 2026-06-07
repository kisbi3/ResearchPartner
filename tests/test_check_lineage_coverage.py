"""Unit tests for .harness/scripts/check_lineage_coverage.py.

Coverage rules under test:
  1. claim node must carry outgoing supports/contradicts edge
  2. non-initial model_version must carry outgoing evolved_from edge
  3. paper node must have incoming cites_paper/reproduces edge
  4. unresolved anomaly must carry outgoing limits edge
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_live(run: Path, nodes: list[dict]) -> None:
    """Write a minimal workflow_map.live.json with the given nodes."""
    data = {
        "generated_at": "2026-01-01T00:00:00Z",
        "maps": [{"id": "test", "title": "Test", "nodes": nodes}],
    }
    run.mkdir(parents=True, exist_ok=True)
    (run / "workflow_map.live.json").write_text(json.dumps(data), encoding="utf-8")


def _check(run: Path) -> list[dict]:
    clc = load("check_lineage_coverage", ROOT / ".harness" / "scripts" / "check_lineage_coverage.py")
    return clc.check(run)


# ---------------------------------------------------------------------------
# 1. Claim with no supports edge → violation
# ---------------------------------------------------------------------------

def test_claim_without_supports_is_violation(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "claim_foo", "node_type": "claim", "lineage_kind": "claim",
         "title": "Foo claim", "graph_links": []},
    ])
    v = _check(run)
    assert any(x["node_id"] == "claim_foo" and "supports" in x["rule"] for x in v)


def test_claim_with_supports_is_clean(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "result_X", "node_type": "validation", "lineage_kind": "result",
         "title": "R X", "graph_links": []},
        {"id": "claim_ok", "node_type": "claim", "lineage_kind": "claim",
         "title": "OK claim", "graph_links": [
             {"from": "claim_ok", "to": "result_X", "relation": "supports"}
         ]},
    ])
    v = _check(run)
    assert not any(x["node_id"] == "claim_ok" for x in v)


# ---------------------------------------------------------------------------
# 2. Non-initial model_version without evolved_from → violation
# ---------------------------------------------------------------------------

def test_v2_without_evolved_from_is_violation(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "model_v2", "node_type": "model", "lineage_kind": "model_version",
         "model_version": "v2", "title": "Model v2", "graph_links": []},
    ])
    v = _check(run)
    assert any(x["node_id"] == "model_v2" and "evolved_from" in x["rule"] for x in v)


def test_v1_without_evolved_from_is_clean(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "model_v1", "node_type": "model", "lineage_kind": "model_version",
         "model_version": "v1", "title": "Model v1", "graph_links": []},
    ])
    v = _check(run)
    assert not any(x["node_id"] == "model_v1" for x in v)


# ---------------------------------------------------------------------------
# 3. Orphan paper (no incoming cites_paper/reproduces) → violation
# ---------------------------------------------------------------------------

def test_orphan_paper_is_violation(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "paper_orphan", "node_type": "paper", "lineage_kind": "paper",
         "paper_id": "orphan", "title": "Orphan", "graph_links": []},
    ])
    v = _check(run)
    assert any(x["node_id"] == "paper_orphan" and "orphan" in x["rule"].lower() for x in v)


def test_paper_with_incoming_cites_is_clean(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "paper_used", "node_type": "paper", "lineage_kind": "paper",
         "paper_id": "used", "title": "Used", "graph_links": []},
        {"id": "decision_x", "node_type": "decision", "lineage_kind": "decision",
         "title": "Use it", "graph_links": [
             {"from": "decision_x", "to": "paper_used", "relation": "cites_paper"}
         ]},
    ])
    v = _check(run)
    assert not any(x["node_id"] == "paper_used" for x in v)


# ---------------------------------------------------------------------------
# 4. Unresolved anomaly without limits → violation
# ---------------------------------------------------------------------------

def test_unresolved_anomaly_without_limits_is_violation(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "anomaly_drift", "node_type": "anomaly", "lineage_kind": "anomaly",
         "phase": "blocked", "title": "Drift", "graph_links": []},
    ])
    v = _check(run)
    assert any(x["node_id"] == "anomaly_drift" and "limits" in x["rule"] for x in v)


def test_resolved_anomaly_without_limits_is_clean(tmp_path):
    run = tmp_path / "runs" / "cov"
    _write_live(run, [
        {"id": "anomaly_done", "node_type": "anomaly", "lineage_kind": "anomaly",
         "phase": "resolved", "title": "Done", "graph_links": []},
    ])
    v = _check(run)
    assert not any(x["node_id"] == "anomaly_done" for x in v)


# ---------------------------------------------------------------------------
# Missing live JSON
# ---------------------------------------------------------------------------

def test_missing_json_reports_one_violation(tmp_path):
    run = tmp_path / "runs" / "no-json"
    run.mkdir(parents=True)
    v = _check(run)
    assert len(v) == 1
    assert "missing" in v[0]["rule"].lower()
