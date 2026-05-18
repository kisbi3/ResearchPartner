"""Unit tests for the lineage-emit path in scripts/workflow_hooks.py.

These tests cover the new build_lineage_packet() mapping and the
emit_lineage_event() end-to-end seeding into workflow_map.live.json.
The auto-emit behavior is what makes the Lineage tab non-empty in
real research scenarios, so a regression here would silently break
the whole feature.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_hooks_module():
    spec = importlib.util.spec_from_file_location(
        "workflow_hooks", ROOT / "scripts" / "workflow_hooks.py"
    )
    module = importlib.util.module_from_spec(spec)
    # workflow_hooks imports update_live_json + update_workflow_diagram, so
    # the scripts dir must be on sys.path when we exec the module.
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    sys.modules["workflow_hooks"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# build_lineage_packet — path → Cartographer JSON packet
# ---------------------------------------------------------------------------

def test_packet_for_model_version():
    wh = load_hooks_module()
    p = wh.build_lineage_packet("docs/model_versions/v3-damped.md")
    u = p["cartographer_update"]
    assert u["lineage_kind"] == "model_version"
    assert u["model_version"] == "v3-damped"
    assert u["node_id"] == "model_v3-damped"
    assert u["node_type"] == "model"


def test_packet_for_paper_review():
    wh = load_hooks_module()
    p = wh.build_lineage_packet("literature/reviews/lacasa2008.md")
    u = p["cartographer_update"]
    assert u["lineage_kind"] == "paper"
    assert u["paper_id"] == "lacasa2008"
    assert u["node_id"] == "paper_lacasa2008"


def test_packet_for_claim():
    wh = load_hooks_module()
    p = wh.build_lineage_packet("docs/claims/hvg-universality.md")
    u = p["cartographer_update"]
    assert u["lineage_kind"] == "claim"
    assert u["requires_researcher_review"] is True


def test_packet_for_figure_includes_thumbnail():
    wh = load_hooks_module()
    p = wh.build_lineage_packet("outputs/figures/fig3.png")
    u = p["cartographer_update"]
    assert u["lineage_kind"] == "figure"
    assert u["thumbnail_path"] == "outputs/figures/fig3.png"


def test_packet_for_error_marks_blocked():
    wh = load_hooks_module()
    p = wh.build_lineage_packet("errors/run-2.err")
    u = p["cartographer_update"]
    assert u["lineage_kind"] == "anomaly"
    assert u["status"] == "blocked"


def test_packet_none_for_cache():
    wh = load_hooks_module()
    # Cache artifacts produce diagram events but no lineage seed.
    assert wh.build_lineage_packet("cache/foo.npy") is None
    # Random other files also return None.
    assert wh.build_lineage_packet("docs/random_note.md") is None


# ---------------------------------------------------------------------------
# emit_lineage_event — end-to-end into workflow_map.live.json
# ---------------------------------------------------------------------------

def test_emit_creates_node_in_live_json(tmp_path):
    wh = load_hooks_module()
    run = tmp_path / "runs" / "2026-01-01-emit-test"
    run.mkdir(parents=True)
    artifact = run / "literature" / "reviews" / "lacasa2008.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Paper review", encoding="utf-8")

    wh.emit_lineage_event(run.resolve(), str(artifact.resolve()))

    data = json.loads((run / "workflow_map.live.json").read_text(encoding="utf-8"))
    node = next(n for n in data["maps"][0]["nodes"] if n["id"] == "paper_lacasa2008")
    assert node["lineage_kind"] == "paper"
    assert node["paper_id"] == "lacasa2008"


def test_emit_silent_on_unknown_extension(tmp_path):
    wh = load_hooks_module()
    run = tmp_path / "runs" / "2026-01-01-silent-test"
    run.mkdir(parents=True)
    artifact = run / "docs" / "random.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("nope", encoding="utf-8")

    # Should not raise and should not create a JSON file.
    wh.emit_lineage_event(run.resolve(), str(artifact.resolve()))
    assert not (run / "workflow_map.live.json").exists()


def test_emit_silent_outside_run_dir(tmp_path):
    wh = load_hooks_module()
    run = tmp_path / "runs" / "real-run"
    run.mkdir(parents=True)
    # Path outside run_dir — relative_to() will raise; should be swallowed.
    outside = tmp_path / "somewhere-else.md"
    outside.write_text("x", encoding="utf-8")
    wh.emit_lineage_event(run.resolve(), str(outside.resolve()))
    # No exception, no JSON written.
    assert not (run / "workflow_map.live.json").exists()
