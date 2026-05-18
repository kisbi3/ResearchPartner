#!/usr/bin/env python3
"""Create a detailed paper-review note inside a research run."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402


def slugify_title(title: str) -> str:
    """Return a lowercase hyphenated ASCII-ish slug for a paper title."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    if not slug:
        raise ValueError("Title must contain at least one letter or number.")
    return slug


def relative_to_run(run_path: Path, path: Path | None) -> str:
    """Return a POSIX-style path relative to the run when possible."""
    if path is None:
        return ""
    try:
        relative = path.resolve().relative_to(run_path.resolve())
    except ValueError:
        return path.as_posix()
    return relative.as_posix()


def markdown_link(label: str, target: str) -> str:
    """Return a Markdown link, preserving empty targets as blank text."""
    if not target:
        return ""
    return f"[{label}]({target})"


def relative_markdown_target(from_path: Path, to_path: Path) -> str:
    """Return a POSIX Markdown target from one artifact to another."""
    return os.path.relpath(Path(to_path), start=Path(from_path).parent).replace(os.sep, "/")


def build_review_note(
    *,
    paper_id: str,
    title: str,
    authors: str = "",
    year: str = "",
    pdf_relative_path: str = "",
    role: str = "",
    pdf_link_target: str = "",
    index_link_target: str = "../index.md",
    replanning_link_target: str = "../../docs/replanning_memo.md",
) -> str:
    """Build the reusable detailed review note body."""
    citation = ", ".join(part for part in [authors, year] if part)
    pdf_text = markdown_link("PDF", pdf_link_target) if pdf_link_target else ""
    run_relative_pdf = f"`{pdf_relative_path}`" if pdf_relative_path else ""
    return f"""# {title}

## Review Metadata

- Paper ID: {paper_id}
- Title: {title}
- Authors / year: {citation}
- Venue:
- DOI / arXiv / URL:
- PDF path: {pdf_text}
- Run-relative PDF path: {run_relative_pdf}
- Review note path:
- Paper Review Index: [literature/index.md]({index_link_target})
- Replanning Memo: [docs/replanning_memo.md]({replanning_link_target})
- Review date:
- Reviewer:
- Status: reading
- Project role: {role}

## Context Summary

This block is the single source of truth for `literature/summary.md`. Keep it concise (one short line per field) so the Lead Agent can load all paper summaries together without loading full reviews. Do not delete the HTML markers; `compile_literature_summary.py` reads between them.

<!-- context-summary:start -->
- **Paper ID**: {paper_id}
- **Title**: {title}
- **Role in project**: <foundation / closest prior / benchmark / method / contradiction>
- **Claim ceiling this paper can support**: <observation / interpretation / mechanism / generalization / unsupported>
- **Novelty impact on our planned claim**: <supports / weakens / contradicts / unrelated / unverified>
- **Reproduction target**: <figure/equation/dataset>; pass criterion: <criterion or 확인 필요>
- **One-sentence takeaway**: <one sentence>
- **When NOT to rely on this paper**: <one short caveat or 확인 필요>
<!-- context-summary:end -->

## 0. Executive Summary

- One-paragraph summary:
- Main contribution:
- Why this paper matters for this project:
- What a future researcher should remember:
- Claim ceiling this paper can support for our project:

## Source Text Extraction

- Extracted text path:
- Extraction command:
- Extraction caveat: PDF text extraction is a reading aid, not evidence by itself. Verify claims against the PDF.

## 1. Research Context and Motivation

- Research background:
- Core problem:
- Why the problem is important:
- Limitations of prior work:
- The paper's research question:
- What to watch for while reading:

## 2. Key Concepts and Definitions

| Concept | Definition | Intuition | Role in Paper | Role in Our Project | Link Candidate |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 3. Methodology

### 3.1 Data, Simulation, or Model Construction

- Data source or simulated system:
- State variables and observables:
- Boundary conditions:
- Initial conditions:
- Parameter ranges:
- Units or nondimensionalization:
- Approximation regime:

### 3.2 Proposed Method

- Method or algorithm:
- Inputs and outputs:
- Step-by-step procedure:
- Hyperparameters, tolerances, grids, timesteps, or sample sizes:
- Random seeds or stochastic elements:
- Implementation details needed for reproduction:

### 3.3 Comparison Methods

- Baselines:
- Alternative models:
- Fairness of comparisons:
- Missing comparisons:

### 3.4 Metrics and Validation

- Metrics:
- Statistical tests or uncertainty estimates:
- Conservation, limiting-case, or dimensional checks:
- Sensitivity or robustness checks:
- Failure criteria:

### 3.5 Equations and Derivations

| Equation | Variables | Assumptions | Units / Dimensions | Role | Reproduction Need |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### 3.6 Methodological Critique

- What assumptions drive the result?
- Which choices are under-justified?
- What would change under another parameter regime?
- What details are missing for reproduction?

## Figure/Table-by-Figure/Table Review

| Figure/Table | What It Shows | Inputs / Parameters | Author's Interpretation | My Interpretation | Reproduction Value | Caveats |
|---|---|---|---|---|---|---|
| Fig. 1 |  |  |  |  |  |  |

## Results Logic

- Main results in order:
- How each result supports the next:
- What the paper claims from the results:
- What the results actually establish:
- Results that are weak, missing, or ambiguous:

## Discussion and Interpretation

- Authors' central interpretation:
- Why the interpretation matters:
- Limitations acknowledged by the authors:
- Limitations not acknowledged:
- Relationship to prior literature:
- Relationship to our planned model, observable, or method:
- Possible overclaims:

## Strengths, Weaknesses, and Open Questions

### Strengths

- 

### Weaknesses

- 

### Open Questions

- 

## Reproduction Extraction

- Candidate reproduction target:
- Target type: figure / table / equation / dataset / benchmark / limiting case
- Required data:
- Required parameters:
- Required code or algorithm details:
- Pass/fail criterion:
- Expected failure modes:
- What this reproduction would validate:
- What it would not validate:

## Novelty and Claim Impact

| Our Planned Claim | Paper Evidence | Impact | Status | Needed Action |
|---|---|---|---|---|
|  |  | supports / weakens / contradicts / unrelated | supported / weak / contradicted / unverified |  |

## Dictionary Notes to Create

| Note Type | Candidate Title | Why Needed | Priority |
|---|---|---|---|
| Concept / Method / Metric / Model / Dataset / Mathematical Tool / Experimental Protocol / Literature Cluster |  |  |  |

## References and Further Reading

- Papers cited by this paper that we should request:
- Papers that cite this paper:
- Adjacent methods or benchmarks:
- Internal notes to link:

## Final Takeaway

- One-sentence summary:
- When to cite this paper:
- When to cite it cautiously:
- How it changes the current research plan:

## Quality Checklist

- [ ] The review is detailed enough to understand the paper's flow without reopening the PDF.
- [ ] Important concepts are defined at first use.
- [ ] Method details include assumptions, parameters, units, and reproduction-critical settings.
- [ ] Each important figure/table is reviewed separately.
- [ ] Author claims and reviewer interpretation are separated.
- [ ] Novelty impact is based on direct PDF evidence or explicitly marked unverified.
- [ ] Reproduction target and pass/fail criterion are explicit.
"""


def append_index_row(
    *,
    index_path: Path,
    paper_id: str,
    title: str,
    authors: str,
    year: str,
    pdf_relative_path: str,
    review_relative_path: str,
    pdf_link_target: str,
    review_link_target: str,
    role: str,
) -> None:
    """Append a paper row to the run-local literature index."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if not index_path.exists():
        index_path.write_text("# Paper Review Index\n\n", encoding="utf-8")

    authors_year = " / ".join(part for part in [authors, year] if part)
    pdf_cell = (
        f"{markdown_link('PDF', pdf_link_target)}<br>`{pdf_relative_path}`"
        if pdf_relative_path
        else ""
    )
    review_cell = f"{markdown_link('Review', review_link_target)}<br>`{review_relative_path}`"
    row = (
        f"| {paper_id} | {title} | {authors_year} | {pdf_cell} | {review_cell} | "
        f"reading | {role} | maybe | unverified |\n"
    )
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write(row)


def create_paper_review(
    *,
    run_path: Path | str,
    paper_id: str,
    title: str,
    authors: str = "",
    year: str = "",
    pdf_path: Path | str | None = None,
    role: str = "",
) -> Path:
    """Create a paper review note and update the run-local paper index."""
    run_path = Path(run_path)
    reviews_dir = run_path / "literature" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify_title(title)
    review_path = reviews_dir / f"{paper_id}-{slug}.md"
    if review_path.exists():
        raise FileExistsError(f"Review already exists: {review_path}")

    pdf = Path(pdf_path) if pdf_path else None
    pdf_relative_path = relative_to_run(run_path, pdf)
    review_relative_path = relative_to_run(run_path, review_path)
    index_path = run_path / "literature" / "index.md"
    pdf_review_link = relative_markdown_target(review_path, pdf) if pdf else ""
    pdf_index_link = relative_markdown_target(index_path, pdf) if pdf else ""
    review_index_link = relative_markdown_target(index_path, review_path)

    review_path.write_text(
        build_review_note(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            pdf_relative_path=pdf_relative_path,
            role=role,
            pdf_link_target=pdf_review_link,
        ),
        encoding="utf-8",
    )
    append_index_row(
        index_path=index_path,
        paper_id=paper_id,
        title=title,
        authors=authors,
        year=year,
        pdf_relative_path=pdf_relative_path,
        review_relative_path=review_relative_path,
        pdf_link_target=pdf_index_link,
        review_link_target=review_index_link,
        role=role,
    )
    return review_path


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
    parser.add_argument("--title", required=True, help="Paper title.")
    parser.add_argument("--authors", default="", help="Author string.")
    parser.add_argument("--year", default="", help="Publication year.")
    parser.add_argument("--pdf", dest="pdf_path", type=Path, help="Path to the paper PDF.")
    parser.add_argument("--role", default="", help="Project role such as benchmark or prior work.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    review_path = create_paper_review(
        run_path=project,
        paper_id=args.paper_id,
        title=args.title,
        authors=args.authors,
        year=args.year,
        pdf_path=args.pdf_path,
        role=args.role,
    )
    print(f"Created {review_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
