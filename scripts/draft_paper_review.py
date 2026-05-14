#!/usr/bin/env python3
"""Draft provisional paper-review notes from extracted PDF text."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SECTION_ALIASES = {
    "abstract": ("abstract",),
    "introduction": ("introduction", "background"),
    "methods": ("methods", "methodology", "materials and methods", "model"),
    "results": ("results", "experiments", "findings"),
    "discussion": ("discussion",),
    "conclusion": ("conclusion", "conclusions"),
}


def normalize_space(text: str) -> str:
    """Collapse whitespace for stable snippets."""
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Return simple sentence-like snippets."""
    compact = normalize_space(text)
    if not compact:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]


def first_snippet(text: str, *, max_sentences: int = 2, max_chars: int = 500) -> str:
    """Return a short human-reviewable snippet."""
    sentences = split_sentences(text)
    snippet = " ".join(sentences[:max_sentences]) if sentences else normalize_space(text)
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 3].rstrip() + "..."
    return snippet


def find_section(text: str, aliases: tuple[str, ...]) -> str:
    """Extract text after the first matching heading until another known heading."""
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip().strip(":").lower()
        if stripped in aliases:
            start = index + 1
            break
    if start is None:
        return ""

    all_headings = {alias for values in SECTION_ALIASES.values() for alias in values}
    end = len(lines)
    for index in range(start, len(lines)):
        stripped = lines[index].strip().strip(":").lower()
        if stripped in all_headings:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def find_lines_containing(text: str, patterns: tuple[str, ...], *, limit: int = 5) -> list[str]:
    """Return lines containing any pattern."""
    matches: list[str] = []
    lowered_patterns = tuple(pattern.lower() for pattern in patterns)
    for line in text.splitlines():
        compact = normalize_space(line)
        if not compact:
            continue
        lowered = compact.lower()
        if any(pattern in lowered for pattern in lowered_patterns):
            matches.append(compact)
        if len(matches) >= limit:
            break
    return matches


def bullet_or_placeholder(value: str) -> str:
    """Format a draft bullet with an uncertainty marker."""
    if value:
        return f"- 확인 필요: {value}"
    return "- 확인 필요: extracted text did not expose a clear candidate."


def build_machine_draft(extracted_text: str, *, extracted_path: Path | str) -> str:
    """Build a provisional review-draft section from extracted text."""
    sections = {
        name: find_section(extracted_text, aliases)
        for name, aliases in SECTION_ALIASES.items()
    }
    figure_lines = find_lines_containing(
        extracted_text,
        ("figure", "fig.", "table"),
        limit=6,
    )
    reproduction_lines = find_lines_containing(
        extracted_text,
        ("benchmark", "reproduce", "dataset", "parameter", "boundary", "sample", "baseline"),
        limit=8,
    )

    figure_block = "\n".join(f"- 확인 필요: {line}" for line in figure_lines)
    if not figure_block:
        figure_block = "- 확인 필요: no figure/table candidate found in extracted text."

    reproduction_block = "\n".join(f"- 확인 필요: {line}" for line in reproduction_lines)
    if not reproduction_block:
        reproduction_block = "- 확인 필요: no candidate reproduction target found in extracted text."

    return f"""## Machine-Assisted Draft From Extracted Text

> 확인 필요: This section is a provisional reading aid generated from extracted text at `{extracted_path}`. It does not establish novelty or validate claims. Verify every statement against the PDF, especially equations, figures, captions, tables, and parameter values.

### Candidate Executive Summary

{bullet_or_placeholder(first_snippet(sections["abstract"]))}

### Candidate Research Context

{bullet_or_placeholder(first_snippet(sections["introduction"], max_sentences=3))}

### Candidate Methodology Notes

{bullet_or_placeholder(first_snippet(sections["methods"], max_sentences=3))}

### Candidate Results Notes

{bullet_or_placeholder(first_snippet(sections["results"], max_sentences=3))}

### Candidate Figure/Table Leads

{figure_block}

### Candidate Reproduction Leads

{reproduction_block}

### Candidate Final Takeaway

{bullet_or_placeholder(first_snippet(sections["conclusion"] or sections["discussion"], max_sentences=2))}

### Required Human Checks

- [ ] Compare every candidate sentence against the PDF.
- [ ] Check equations, variables, and units manually.
- [ ] Check figure/table captions manually.
- [ ] Mark unsupported novelty implications as `unverified`.
- [ ] Convert at most one candidate reproduction lead into a candidate reproduction target.
"""


def replace_or_append_machine_draft(review_text: str, draft_section: str) -> str:
    """Replace an existing machine draft section or append it after source extraction."""
    marker = "## Machine-Assisted Draft From Extracted Text"
    following_markers = [
        "\n## 1. Research Context and Motivation",
        "\n## 2. Key Concepts and Definitions",
    ]
    if marker in review_text:
        before = review_text.split(marker, 1)[0]
        rest = review_text.split(marker, 1)[1]
        next_positions = [
            rest.find(next_marker)
            for next_marker in following_markers
            if rest.find(next_marker) != -1
        ]
        if next_positions:
            pos = min(next_positions)
            return before + draft_section + rest[pos:]
        return before + draft_section

    source_marker = "\n## 1. Research Context and Motivation"
    if source_marker in review_text:
        before, after = review_text.split(source_marker, 1)
        return before.rstrip() + "\n\n" + draft_section + source_marker + after
    return review_text.rstrip() + "\n\n" + draft_section


def update_review_draft(
    *,
    review_path: Path | str,
    extracted_text_path: Path | str,
) -> Path:
    """Update a paper review note with a provisional machine-assisted draft."""
    review_path = Path(review_path)
    extracted_text_path = Path(extracted_text_path)
    extracted_text = extracted_text_path.read_text(encoding="utf-8")
    review_text = review_path.read_text(encoding="utf-8")
    draft = build_machine_draft(
        extracted_text,
        extracted_path=extracted_text_path.as_posix(),
    )
    review_path.write_text(
        replace_or_append_machine_draft(review_text, draft),
        encoding="utf-8",
    )
    return review_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path, help="Paper review note path.")
    parser.add_argument(
        "--extracted-text",
        required=True,
        type=Path,
        help="Extracted PDF text artifact.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    update_review_draft(
        review_path=args.review,
        extracted_text_path=args.extracted_text,
    )
    print(f"Updated {args.review}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

