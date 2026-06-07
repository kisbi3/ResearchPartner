import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "scaffold_paper_review.py"
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
def test_scaffold_paper_review_creates_review_and_updates_index(tmp_path):
    run_path = create_run(tmp_path)
    scaffold = load_module("scaffold_paper_review", SCRIPT)
    pdf_path = run_path / "literature" / "pdfs" / "example.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    review_path = scaffold.create_paper_review(
        run_path=run_path,
        paper_id="P1",
        title="Example Paper: A Useful Benchmark",
        authors="Ada Lovelace and Emmy Noether",
        year="2026",
        pdf_path=pdf_path,
        role="benchmark",
    )

    assert review_path == run_path / "literature" / "reviews" / "P1-example-paper-a-useful-benchmark.md"
    assert review_path.exists()
    review_text = review_path.read_text(encoding="utf-8")
    assert "Paper ID: P1" in review_text
    assert "Title: Example Paper: A Useful Benchmark" in review_text
    assert "PDF path: [PDF](../pdfs/example.pdf)" in review_text
    assert "Run-relative PDF path: `literature/pdfs/example.pdf`" in review_text
    assert "Paper Review Index: [literature/index.md](../index.md)" in review_text
    assert "Replanning Memo: [docs/literature/replanning_memo.md](../../docs/literature/replanning_memo.md)" in review_text
    assert "Figure/Table-by-Figure/Table Review" in review_text
    assert "Reproduction Extraction" in review_text
    assert "Source Text Extraction" in review_text

    index_text = (run_path / "literature" / "index.md").read_text(encoding="utf-8")
    assert "Example Paper: A Useful Benchmark" in index_text
    assert "[PDF](pdfs/example.pdf)" in index_text
    assert "[Review](reviews/P1-example-paper-a-useful-benchmark.md)" in index_text
    assert "`literature/pdfs/example.pdf`" in index_text
    assert "`literature/reviews/P1-example-paper-a-useful-benchmark.md`" in index_text
    assert "benchmark" in index_text


def test_scaffold_paper_review_refuses_duplicate_review(tmp_path):
    run_path = create_run(tmp_path)
    scaffold = load_module("scaffold_paper_review", SCRIPT)

    scaffold.create_paper_review(
        run_path=run_path,
        paper_id="P1",
        title="Duplicate Paper",
    )

    with pytest.raises(FileExistsError):
        scaffold.create_paper_review(
            run_path=run_path,
            paper_id="P1",
            title="Duplicate Paper",
        )
