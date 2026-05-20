#!/usr/bin/env python3
"""Check whether a paper review note is ready for literature replanning."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


REQUIRED_SECTIONS = (
    "Review Metadata",
    "Context Summary",
    "Source Text Extraction",
    "0. Executive Summary",
    "1. Research Context and Motivation",
    "2. Key Concepts and Definitions",
    "3. Methodology",
    "Figure/Table-by-Figure/Table Review",
    "Results Logic",
    "Discussion and Interpretation",
    "Reproduction Extraction",
    "Novelty and Claim Impact",
    "Final Takeaway",
    "Quality Checklist",
)

REQUIRED_PATTERNS = (
    ("PDF link", r"PDF path:\s*\[PDF\]\("),
    ("run-relative PDF path", r"Run-relative PDF path:\s*`?literature/pdfs/"),
    ("Paper Review Index link", r"Paper Review Index:\s*\[literature/index\.md\]\("),
    ("Replanning Memo link", r"Replanning Memo:\s*\[docs/(?:literature/)?replanning_memo\.md\]\("),
    ("Extracted text link", r"Extracted text path:\s*\[Extracted text\]\("),
    (
        "PDF extraction caveat",
        r"PDF text extraction is a reading aid, not evidence by itself",
    ),
    ("uncertainty marker", r"확인 필요|unverified"),
    ("reproduction pass/fail criterion", r"Pass/fail criterion:\s*\S"),
    ("context-summary start marker", r"<!--\s*context-summary:start\s*-->"),
    ("context-summary end marker", r"<!--\s*context-summary:end\s*-->"),
)


@dataclass(frozen=True)
class ReviewQualityResult:
    """Quality-check result for one paper review."""

    path: Path
    status: str
    missing: list[str]
    warnings: list[str]


def has_heading(text: str, heading: str) -> bool:
    """Return whether a Markdown heading exists."""
    return bool(re.search(rf"^#+\s+{re.escape(heading)}\s*$", text, flags=re.MULTILINE))


def find_unchecked_checklist_items(text: str) -> list[str]:
    """Return unchecked checklist item labels."""
    return [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^-\s+\[\s\]\s+", line.strip())
    ]


def check_review_quality(path: Path | str) -> ReviewQualityResult:
    """Check one review note for required sections, links, and caveats."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    missing: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if not has_heading(text, section):
            missing.append(section)

    for label, pattern in REQUIRED_PATTERNS:
        if not re.search(pattern, text, flags=re.IGNORECASE):
            missing.append(label)

    if find_unchecked_checklist_items(text):
        warnings.append("unchecked checklist item")

    status = "pass" if not missing and not warnings else "fail"
    return ReviewQualityResult(path=path, status=status, missing=missing, warnings=warnings)


def format_result(result: ReviewQualityResult) -> str:
    """Return a compact Markdown quality report."""
    lines = [
        "# Paper Review Quality Check",
        "",
        f"- Review: `{result.path}`",
        f"- Status: {result.status}",
        "",
        "| Type | Item |",
        "|---|---|",
    ]
    if not result.missing and not result.warnings:
        lines.append("| pass | none |")
    for item in result.missing:
        lines.append(f"| missing | {item} |")
    for item in result.warnings:
        lines.append(f"| warning | {item} |")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path, help="Paper review Markdown file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = check_review_quality(args.review)
    print(format_result(result))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
