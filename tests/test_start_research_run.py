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

    # ── Gate artifacts (docs/gates/) ─────────────────────────────────────────
    assert (run_path / "docs" / "gates" / "orient_note.md").exists()
    assert (run_path / "docs" / "gates" / "interview_notes.md").exists()
    assert (run_path / "docs" / "gates" / "baseline_registry.md").exists()
    assert (run_path / "docs" / "gates" / "validation_log.md").exists()

    # ── Plan artifacts (docs/plan/) ───────────────────────────────────────────
    assert (run_path / "docs" / "plan" / "research_plan.md").exists()
    assert (run_path / "docs" / "plan" / "model_spec.md").exists()
    assert (run_path / "docs" / "plan" / "baseline_strategy.md").exists()

    # ── Process artifacts (docs/process/) ────────────────────────────────────
    assert (run_path / "docs" / "process" / "live_workflow_diagram.md").exists()
    assert (run_path / "docs" / "process" / "cartographer_update_template.md").exists()
    assert (run_path / "docs" / "process" / "researcher_review_log.md").exists()
    assert (run_path / "docs" / "process" / "research_retrospective.md").exists()

    # ── Literature meta (docs/literature/) ───────────────────────────────────
    assert (run_path / "docs" / "literature" / "literature_review_plan.md").exists()
    assert (run_path / "docs" / "literature" / "paper_request_queue.md").exists()
    assert (run_path / "docs" / "literature" / "replanning_memo.md").exists()

    # ── Literature files ──────────────────────────────────────────────────────
    assert (run_path / "literature" / "pdfs").is_dir()
    assert (run_path / "literature" / "reviews").is_dir()
    assert (run_path / "literature" / "extracted_text").is_dir()
    assert (run_path / "literature" / "index.md").exists()

    # ── Runtime directories ───────────────────────────────────────────────────
    assert (run_path / "src").is_dir()
    assert (run_path / "outputs" / "figures").is_dir()
    assert (run_path / "outputs" / "data").is_dir()
    assert (run_path / "outputs" / "tables").is_dir()
    assert (run_path / "cache").is_dir()
    assert (run_path / "logs").is_dir()
    assert (run_path / "errors").is_dir()

    # ── Root files ────────────────────────────────────────────────────────────
    assert (run_path / "research_run_packet.md").exists()
    assert (run_path / ".gitignore").exists()

    gitignore = (run_path / ".gitignore").read_text(encoding="utf-8")
    assert "cache/" in gitignore
    assert "logs/" in gitignore
    assert "errors/" in gitignore

    workflow = (run_path / "docs" / "process" / "live_workflow_diagram.md").read_text(encoding="utf-8")
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
    assert "section-by-section paper review" in packet
    assert "Code links" in packet
    assert "Result links" in packet
    assert "Interpretation links" in packet
    readme = (run_path / "README.md").read_text(encoding="utf-8")
    assert "workflow_map.html" in readme
    assert "Current Run Dashboard" in readme

    review_plan = (run_path / "docs" / "literature" / "literature_review_plan.md").read_text(
        encoding="utf-8"
    )
    assert "Detailed Paper Review Notes" in review_plan
    assert "Figure/Table-by-Figure/Table Review" in review_plan
    assert "Reproduction Extraction" in review_plan


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
