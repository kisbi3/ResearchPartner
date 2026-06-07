import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESS_SCRIPT = ROOT / ".harness" / "scripts" / "process_paper_for_review.py"
INIT_SCRIPT = ROOT / ".harness" / "scripts" / "init_research_project.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def create_run(tmp_path: Path) -> Path:
    init = load_module("init_research_project", INIT_SCRIPT)
    return init.scaffold_project(tmp_path / "project")
def test_process_paper_creates_review_text_artifact_and_draft(tmp_path):
    processor = load_module("process_paper_for_review", PROCESS_SCRIPT)
    run_path = create_run(tmp_path)
    pdf_path = run_path / "literature" / "pdfs" / "example.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    result = processor.process_paper(
        run_path=run_path,
        paper_id="P1",
        title="Example Paper: A Useful Benchmark",
        authors="Ada Lovelace",
        year="2026",
        pdf_path=pdf_path,
        role="benchmark",
        extracted_text=(
            "Abstract\n"
            "We study a benchmark model for anomalous diffusion.\n"
            "Introduction\n"
            "The key problem is robust estimation from short trajectories.\n"
            "Methods\n"
            "We simulate particles with reflecting boundary conditions.\n"
            "Results\n"
            "Figure 1 shows small-sample bias.\n"
            "Conclusion\n"
            "The benchmark is a candidate reproduction target."
        ),
    )

    assert result.review_path == run_path / "literature" / "reviews" / "P1-example-paper-a-useful-benchmark.md"
    assert result.extracted_text_path == run_path / "literature" / "extracted_text" / "P1-example.txt"
    assert result.review_path.exists()
    assert result.extracted_text_path.exists()

    review_text = result.review_path.read_text(encoding="utf-8")
    assert "Source Text Extraction" in review_text
    assert "[Extracted text](../extracted_text/P1-example.txt)" in review_text
    assert "Machine-Assisted Draft From Extracted Text" in review_text
    assert "reflecting boundary conditions" in review_text
    assert "does not establish novelty or validate claims" in review_text

    index_text = (run_path / "literature" / "index.md").read_text(encoding="utf-8")
    assert "Example Paper: A Useful Benchmark" in index_text
    assert "[PDF](pdfs/example.pdf)" in index_text
    assert "[Review](reviews/P1-example-paper-a-useful-benchmark.md)" in index_text
    assert "`literature/reviews/P1-example-paper-a-useful-benchmark.md`" in index_text
