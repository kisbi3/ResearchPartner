"""Unit tests for lineage-specific behavior in scripts/sync_workflow.py.

Covers:
  - find_broken_edges(): broken graph_links.to and dangling edges
  - --validate-edges CLI flag: returns 2 on broken edges, 0 on clean
  - YAML front-matter parsing: paper, model_version, claim nodes
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_sync():
    spec = importlib.util.spec_from_file_location(
        "sync_workflow", ROOT / "scripts" / "sync_workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_workflow"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _scaffold_project(project: Path) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / ".research-harness").write_text("v3")
    (project / "docs" / "process").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "process" / "live_workflow_diagram.md").write_text(
        "# Live Workflow Diagram\n\n"
        "## Active Step\n\n- Current step: (not started)\n- Current owner: lead-agent\n- Last update: never\n\n"
        "## Gate Status\n\n| Gate | Status | Note |\n|---|---|---|\n\n"
        "## In-Flight Tasks\n\n| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n|---|---|---|---|---|---|\n\n"
        "## Real-Time Event Log\n\n"
    )


def _write_live(project: Path, nodes: list[dict]) -> None:
    data = {
        "generated_at": "2026-01-01T00:00:00Z",
        "maps": [{"id": "test", "title": "Test", "nodes": nodes}],
    }
    (project / "workflow_map.live.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Broken-edge linter
# ---------------------------------------------------------------------------

def test_find_broken_edges_clean(tmp_path):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    _write_live(project, [
        {"id": "a", "node_type": "decision", "lineage_kind": "decision", "graph_links": []},
        {"id": "b", "node_type": "decision", "lineage_kind": "decision", "graph_links": [
            {"from": "b", "to": "a", "relation": "depends_on"}
        ]},
    ])
    assert sw.find_broken_edges(project) == []


def test_find_broken_edges_catches_typo(tmp_path):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    _write_live(project, [
        {"id": "claim_x", "node_type": "claim", "lineage_kind": "claim", "graph_links": [
            {"from": "claim_x", "to": "result_typo", "relation": "supports"}
        ]},
    ])
    broken = sw.find_broken_edges(project)
    assert any(b["field"] == "graph_links.to" and b["target"] == "result_typo" for b in broken)


def test_find_broken_edges_missing_json(tmp_path):
    sw = _load_sync()
    project = tmp_path / "proj"
    project.mkdir(parents=True)
    # No workflow_map.live.json → returns empty list, doesn't raise.
    assert sw.find_broken_edges(project) == []


# ---------------------------------------------------------------------------
# --validate-edges CLI flag
# ---------------------------------------------------------------------------

def test_cli_validate_edges_clean_returns_zero(tmp_path, monkeypatch):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    # Seed a paper review with no cross-referential edges — no broken refs.
    (project / "literature").mkdir()
    (project / "literature" / "reviews").mkdir()
    (project / "literature" / "reviews" / "clean.md").write_text(
        "---\nlineage:\n  node_type: paper\n  lineage_kind: paper\n  paper_id: clean\n---\n"
    )
    monkeypatch.setattr(sys, "argv", [
        "sync_workflow.py", "--project", str(project), "--validate-edges",
    ])
    rc = sw.main()
    assert rc == 0


def test_cli_validate_edges_broken_returns_two(tmp_path, monkeypatch):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    # Seed a claim with a supports edge pointing at a non-existent result node.
    (project / "docs" / "claims").mkdir(parents=True)
    (project / "docs" / "claims" / "claim_x.md").write_text(
        "---\nlineage:\n  node_type: claim\n  lineage_kind: claim\n"
        "  supports:\n    - result_ghost\n---\n"
    )
    monkeypatch.setattr(sys, "argv", [
        "sync_workflow.py", "--project", str(project), "--validate-edges",
    ])
    rc = sw.main()
    assert rc == 2


# ---------------------------------------------------------------------------
# YAML front-matter parsing
# ---------------------------------------------------------------------------

def test_frontmatter_paper_node(tmp_path):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    (project / "literature").mkdir()
    (project / "literature" / "reviews").mkdir()
    (project / "literature" / "reviews" / "smith2020.md").write_text(
        "---\nlineage:\n  node_type: paper\n  lineage_kind: paper\n  paper_id: smith2020\n---\n\n# Review\n"
    )
    out = sw.sync(project)
    data = json.loads(out.read_text())
    nodes = data["maps"][0]["nodes"]
    assert any(n.get("lineage_kind") == "paper" and n.get("paper_id") == "smith2020" for n in nodes)


# ---------------------------------------------------------------------------
# Gate status inference via dedicated check scripts
# ---------------------------------------------------------------------------

def test_derive_gate_status_orient_pass(tmp_path):
    """orient_note.md with all 4 sections filled → gate shows 'pass'."""
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    (project / "docs" / "gates").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "gates" / "orient_note.md").write_text(
        "## Task Classification\n- New model\n\n"
        "## Responsible Role\n- Lead Agent\n\n"
        "## First Professor Question\nWhat is the research question?\n\n"
        "## Researcher Answer\nWe want to study financial time series.\n"
    )
    out = sw.sync(project)
    data = json.loads(out.read_text())
    nodes = data["maps"][0]["nodes"]
    gate_node = next(
        (n for n in nodes if n.get("id") == "gate_orient_gate"), None
    )
    assert gate_node is not None, "orient gate node missing from live JSON"
    assert gate_node["gate_status"] == "pass", (
        f"expected 'pass' but got '{gate_node['gate_status']}'"
    )


def test_derive_gate_status_orient_pending_when_blank(tmp_path):
    """orient_note.md with empty sections → gate stays 'pending'."""
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    (project / "docs" / "gates").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "gates" / "orient_note.md").write_text(
        "## Task Classification\n\n"
        "## Responsible Role\n\n"
        "## First Professor Question\n\n"
        "## Researcher Answer\n"
    )
    out = sw.sync(project)
    data = json.loads(out.read_text())
    nodes = data["maps"][0]["nodes"]
    gate_node = next(
        (n for n in nodes if n.get("id") == "gate_orient_gate"), None
    )
    assert gate_node is not None
    assert gate_node["gate_status"] == "pending"


def test_frontmatter_model_version_node(tmp_path):
    sw = _load_sync()
    project = tmp_path / "proj"
    _scaffold_project(project)
    (project / "docs" / "model_versions").mkdir(parents=True)
    (project / "docs" / "model_versions" / "v1.md").write_text(
        "---\nlineage:\n  node_type: model_version\n  lineage_kind: model_version\n  model_version: v1\n---\n\n# Model v1\n"
    )
    out = sw.sync(project)
    data = json.loads(out.read_text())
    nodes = data["maps"][0]["nodes"]
    assert any(n.get("lineage_kind") == "model_version" and n.get("model_version") == "v1" for n in nodes)
