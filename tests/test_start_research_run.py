import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "start_research_run.py"


def load_scaffolder():
    spec = importlib.util.spec_from_file_location("start_research_run", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["start_research_run"] = module
    spec.loader.exec_module(module)
    return module


def test_slugify_name_uses_lowercase_hyphenated_ascii():
    scaffolder = load_scaffolder()

    assert scaffolder.slugify_name("  1D Diffusion: Mode Decay!  ") == "1d-diffusion-mode-decay"


def test_create_run_copies_templates_and_initial_docs(tmp_path):
    scaffolder = load_scaffolder()

    run_path = scaffolder.create_run(
        name="1D Diffusion Mode Decay",
        date_text="2026-05-14",
        runs_root=tmp_path,
    )

    assert run_path == tmp_path / "2026-05-14-1d-diffusion-mode-decay"
    assert (run_path / "docs" / "live_workflow_diagram.md").exists()
    assert (run_path / "docs" / "cartographer_update_template.md").exists()
    assert (run_path / "research_run_packet.md").exists()
    assert (run_path / "outputs").is_dir()
    assert (run_path / "literature" / "pdfs").is_dir()
    assert (run_path / "docs" / "research_plan.md").exists()
    assert (run_path / "docs" / "literature_review_plan.md").exists()
    assert (run_path / "docs" / "paper_request_queue.md").exists()
    assert (run_path / "docs" / "replanning_memo.md").exists()
    assert (run_path / "docs" / "baseline_registry.md").exists()
    assert (run_path / "docs" / "validation_log.md").exists()
    assert (run_path / "docs" / "researcher_review_log.md").exists()
    assert (run_path / "docs" / "research_retrospective.md").exists()

    workflow = (run_path / "docs" / "live_workflow_diagram.md").read_text(encoding="utf-8")
    packet = (run_path / "research_run_packet.md").read_text(encoding="utf-8")
    assert "Diagram/Cartographer Agent" in workflow
    assert "Cartographer Update Events" in workflow
    assert "Link Status" in workflow
    assert "Evidence Strength" in workflow
    assert "Researcher Checkpoint Marker" in workflow
    assert "Artifact Preview" in workflow
    assert "Completion Conference" in packet
    assert "Live Linked Research Graph" in packet
    assert "Literature Replanning Loop" in packet
    assert "researcher-provided PDFs" in packet
    assert "Code links" in packet
    assert "Result links" in packet
    assert "Interpretation links" in packet


def test_create_run_refuses_to_overwrite_existing_run(tmp_path):
    scaffolder = load_scaffolder()
    scaffolder.create_run(
        name="Existing Run",
        date_text="2026-05-14",
        runs_root=tmp_path,
    )

    with pytest.raises(FileExistsError):
        scaffolder.create_run(
            name="Existing Run",
            date_text="2026-05-14",
            runs_root=tmp_path,
        )
