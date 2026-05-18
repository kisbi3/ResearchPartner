#!/usr/bin/env python3
"""Extract PDF text for a paper review and link it from the review note."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402


def relative_to_run(run_path: Path, path: Path) -> str:
    """Return a POSIX-style path relative to the run when possible."""
    try:
        return path.resolve().relative_to(run_path.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def relative_markdown_target(from_path: Path, to_path: Path) -> str:
    """Return a POSIX Markdown target from one artifact to another."""
    return os.path.relpath(Path(to_path), start=Path(from_path).parent).replace(os.sep, "/")


def review_slug_from_pdf(pdf_path: Path) -> str:
    """Return a stable slug based on the PDF file stem."""
    stem = pdf_path.stem.strip()
    return stem or "paper"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF with pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF text extraction.") from exc

    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        chunks.append(f"\n\n--- Page {index} ---\n\n{page_text.strip()}")
    return "\n".join(chunks).strip()


def replace_or_append_source_section(
    review_text: str,
    *,
    extracted_relative_path: str,
    extracted_link_target: str,
    command_hint: str,
) -> str:
    """Update the Source Text Extraction section in a review note."""
    section = (
        "## Source Text Extraction\n\n"
        f"- Extracted text path: [Extracted text]({extracted_link_target})\n"
        f"- Run-relative extracted text path: `{extracted_relative_path}`\n"
        f"- Extraction command: `{command_hint}`\n"
        "- Extraction caveat: PDF text extraction is a reading aid, not evidence by itself. "
        "Verify claims against the PDF.\n"
    )
    marker = "## Source Text Extraction"
    next_marker = "\n## 1. Research Context and Motivation"
    if marker in review_text and next_marker in review_text:
        before = review_text.split(marker, 1)[0]
        after = review_text.split(next_marker, 1)[1]
        return before + section + next_marker + after
    return review_text.rstrip() + "\n\n" + section


def write_extracted_text(
    *,
    run_path: Path | str,
    paper_id: str,
    pdf_path: Path | str,
    review_path: Path | str,
    text: str,
) -> Path:
    """Write extracted text and link it from the paper review note."""
    run_path = Path(run_path)
    pdf_path = Path(pdf_path)
    review_path = Path(review_path)
    text_dir = run_path / "literature" / "extracted_text"
    text_dir.mkdir(parents=True, exist_ok=True)

    text_path = text_dir / f"{paper_id}-{review_slug_from_pdf(pdf_path)}.txt"
    header = (
        f"# Extracted text for {paper_id}\n"
        f"# Source PDF: [PDF]({relative_markdown_target(text_path, pdf_path)})\n"
        f"# Run-relative source PDF: {relative_to_run(run_path, pdf_path)}\n"
        f"# Review note: [Review]({relative_markdown_target(text_path, review_path)})\n"
        f"# Run-relative review note: {relative_to_run(run_path, review_path)}\n"
        "# Caveat: PDF text extraction may omit equations, captions, tables, and layout.\n\n"
    )
    text_path.write_text(header + text.strip() + "\n", encoding="utf-8")

    extracted_relative_path = relative_to_run(run_path, text_path)
    extracted_link_target = relative_markdown_target(review_path, text_path)
    command_hint = (
        "python scripts/extract_paper_text.py "
        f"--run {run_path} --paper-id {paper_id} --pdf {pdf_path} --review {review_path}"
    )
    review_text = review_path.read_text(encoding="utf-8")
    review_path.write_text(
        replace_or_append_source_section(
            review_text,
            extracted_relative_path=extracted_relative_path,
            extracted_link_target=extracted_link_target,
            command_hint=command_hint,
        ),
        encoding="utf-8",
    )
    return text_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory. Default: walk up from cwd looking for "
             "the `.research-harness` marker. `--run` kept as alias for one release.",
    )
    parser.add_argument("--paper-id", required=True, help="Stable paper ID such as P1.")
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the paper PDF.")
    parser.add_argument("--review", required=True, type=Path, help="Paper review note path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = extract_pdf_text(args.pdf)
    text_path = write_extracted_text(
        run_path=project,
        paper_id=args.paper_id,
        pdf_path=args.pdf,
        review_path=args.review,
        text=text,
    )
    print(f"Created {text_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
