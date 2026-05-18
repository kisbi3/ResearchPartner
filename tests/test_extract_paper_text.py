import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


def create_review(tmp_path: Path):
    init = load_module("init_research_project", INIT_SCRIPT)
    review_scaffolder = load_module("scaffold_paper_review", SCAFFOLD_SCRIPT)
    run_path = init.scaffold_project(tmp_path / "project")
    pdf_path = run_path / "literature" / "pdfs" / "example.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    review_path = review_scaffolder.create_paper_review(
        run_path=run_path,
        paper_id="P1",
        title="Example Paper",
        pdf_path=pdf_path,
    )
    return run_path, pdf_path, review_path


def test_write_extracted_text_creates_source_artifact_and_links_review(tmp_path):
    extractor = load_module("extract_paper_text", EXTRACT_SCRIPT)
    run_path, pdf_path, review_path = create_review(tmp_path)

    text_path = extractor.write_extracted_text(
        run_path=run_path,
        paper_id="P1",
        pdf_path=pdf_path,
        review_path=review_path,
        text="Introduction\nThis paper studies a benchmark.\nMethods\nWe use a toy model.",
    )

    assert text_path == run_path / "literature" / "extracted_text" / "P1-example.txt"
    assert text_path.exists()
    assert "This paper studies a benchmark" in text_path.read_text(encoding="utf-8")

    review_text = review_path.read_text(encoding="utf-8")
    assert "Source Text Extraction" in review_text
    assert "[Extracted text](../extracted_text/P1-example.txt)" in review_text
    assert "Run-relative extracted text path: `literature/extracted_text/P1-example.txt`" in review_text
    assert "PDF text extraction is a reading aid, not evidence by itself" in review_text

    extracted_text = text_path.read_text(encoding="utf-8")
    assert "Source PDF: [PDF](../pdfs/example.pdf)" in extracted_text
    assert "Review note: [Review](../reviews/P1-example-paper.md)" in extracted_text
