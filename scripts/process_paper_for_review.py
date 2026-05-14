#!/usr/bin/env python3
"""Run the paper-review preparation pipeline for one paper."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import draft_paper_review
import extract_paper_text
import scaffold_paper_review


@dataclass(frozen=True)
class ProcessedPaper:
    """Paths created by the paper review preparation pipeline."""

    review_path: Path
    extracted_text_path: Path


def process_paper(
    *,
    run_path: Path | str,
    paper_id: str,
    title: str,
    authors: str = "",
    year: str = "",
    pdf_path: Path | str,
    role: str = "",
    extracted_text: str | None = None,
) -> ProcessedPaper:
    """Create a review note, extract text, and insert a provisional draft."""
    run_path = Path(run_path)
    pdf_path = Path(pdf_path)
    review_path = scaffold_paper_review.create_paper_review(
        run_path=run_path,
        paper_id=paper_id,
        title=title,
        authors=authors,
        year=year,
        pdf_path=pdf_path,
        role=role,
    )
    text = extracted_text
    if text is None:
        text = extract_paper_text.extract_pdf_text(pdf_path)
    extracted_text_path = extract_paper_text.write_extracted_text(
        run_path=run_path,
        paper_id=paper_id,
        pdf_path=pdf_path,
        review_path=review_path,
        text=text,
    )
    draft_paper_review.update_review_draft(
        review_path=review_path,
        extracted_text_path=extracted_text_path,
    )
    return ProcessedPaper(
        review_path=review_path,
        extracted_text_path=extracted_text_path,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, help="Research run directory.")
    parser.add_argument("--paper-id", required=True, help="Stable paper ID such as P1.")
    parser.add_argument("--title", required=True, help="Paper title.")
    parser.add_argument("--authors", default="", help="Author string.")
    parser.add_argument("--year", default="", help="Publication year.")
    parser.add_argument("--pdf", required=True, dest="pdf_path", type=Path, help="Path to the paper PDF.")
    parser.add_argument("--role", default="", help="Project role such as benchmark or prior work.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = process_paper(
        run_path=args.run,
        paper_id=args.paper_id,
        title=args.title,
        authors=args.authors,
        year=args.year,
        pdf_path=args.pdf_path,
        role=args.role,
    )
    print(f"Review: {result.review_path}")
    print(f"Extracted text: {result.extracted_text_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

