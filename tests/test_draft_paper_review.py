import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT_SCRIPT = ROOT / "scripts" / "draft_paper_review.py"
EXTRACT_SCRIPT = ROOT / "scripts" / "extract_paper_text.py"
SCAFFOLD_SCRIPT = ROOT / "scripts" / "scaffold_paper_review.py"
INIT_SCRIPT = ROOT / "scripts" / "init_research_project.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def create_review_with_extracted_text(tmp_path: Path):
    init = load_module("init_research_project", INIT_SCRIPT)
    review_scaffolder = load_module("scaffold_paper_review", SCAFFOLD_SCRIPT)
    extractor = load_module("extract_paper_text", EXTRACT_SCRIPT)
    run_path = init.scaffold_project(tmp_path / "project")
    pdf_path = run_path / "literature" / "pdfs" / "example.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    review_path = review_scaffolder.create_paper_review(
        run_path=run_path,
        paper_id="P1",
        title="Example Paper",
        pdf_path=pdf_path,
    )
    text_path = extractor.write_extracted_text(
        run_path=run_path,
        paper_id="P1",
        pdf_path=pdf_path,
        review_path=review_path,
        text=(
            "Abstract\n"
            "We study a benchmark model for anomalous diffusion.\n"
            "Introduction\n"
            "The key problem is robust estimation from short trajectories.\n"
            "Methods\n"
            "We simulate particles with reflecting boundary conditions and compare baselines.\n"
            "Results\n"
            "Figure 1 shows that the estimator is biased at small sample size.\n"
            "Conclusion\n"
            "The benchmark should be reproduced before stronger claims are made."
        ),
    )
    return review_path, text_path


def test_draft_review_inserts_provisional_sections_from_extracted_text(tmp_path):
    drafter = load_module("draft_paper_review", DRAFT_SCRIPT)
    review_path, text_path = create_review_with_extracted_text(tmp_path)

    drafter.update_review_draft(
        review_path=review_path,
        extracted_text_path=text_path,
    )

    review_text = review_path.read_text(encoding="utf-8")
    assert "## Machine-Assisted Draft From Extracted Text" in review_text
    assert "확인 필요" in review_text
    assert "robust estimation from short trajectories" in review_text
    assert "reflecting boundary conditions" in review_text
    assert "Figure 1" in review_text
    assert "candidate reproduction target" in review_text
    assert "does not establish novelty or validate claims" in review_text


def test_draft_review_replaces_existing_machine_draft(tmp_path):
    drafter = load_module("draft_paper_review", DRAFT_SCRIPT)
    review_path, text_path = create_review_with_extracted_text(tmp_path)

    drafter.update_review_draft(review_path=review_path, extracted_text_path=text_path)
    drafter.update_review_draft(review_path=review_path, extracted_text_path=text_path)

    review_text = review_path.read_text(encoding="utf-8")
    assert review_text.count("## Machine-Assisted Draft From Extracted Text") == 1

