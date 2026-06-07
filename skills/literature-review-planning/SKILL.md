---
name: literature-review-planning
description: Use before full research execution when a project needs literature discovery, researcher-provided PDFs, novelty assessment, reproduction target selection, or PaperQA-style review.
---

# Literature Review Planning Skill

Use this skill between professor-interview and model-specification.

## Prerequisites

Before starting:

1. Confirm `docs/gates/interview_notes.md` exists and the Interview Gate passes (`python .harness/scripts/check_interview_recorded.py --project <project-dir>`). If not, complete the professor-interview skill first.

## Skipping This Step

If the literature review is genuinely not needed for this iteration (e.g. reproducing a known result with well-understood prior work), the researcher may skip this step by creating `docs/literature/literature_skip_waiver.md` with a one-line reason:

```
Skipping literature review: reproducing Fourier (1822) heat equation — prior work is fully known and no novelty is claimed.
```

The Literature Gate (`python .harness/scripts/check_literature_reviewed.py --project <project-dir>`) passes on either a completed review or a waiver file with content. A skip lowers the claim ceiling to at most `interpretation` for this iteration. The goal is not to let an LLM invent a literature review; the goal is to make the researcher's paper access and judgment part of the workflow before simulations, figures, or manuscript claims begin.

## Goal

Create an iterative literature replanning loop that turns paper requests, researcher-provided PDFs, direct paper review, novelty mapping, and reproduction target selection into a stronger second-stage research plan.

## Required Loop

Repeat this loop until the Lead Agent marks the plan ready or the researcher explicitly waives the literature gate:

1. **Question framing**: state the research question, physical system, observable, and candidate claim.
2. **Paper request**: ask the researcher to collect specific PDFs that the LLM cannot access directly, using institutional access when needed.
3. **Paper intake**: record each PDF path, citation metadata, access status, relevance, and whether it has been read.
4. **Direct review**: create one detailed review note per important paper in `literature/reviews/`. The note must be a section-by-section paper review, not a short abstract summary. It should reconstruct the paper's context, concepts, method, equations, assumptions, units, figures/tables, limitations, and reusable research value. Each review note must fill in the **`Context Summary`** block (between the `<!-- context-summary:start -->` and `<!-- context-summary:end -->` HTML markers) — this block is the compact form the Lead Agent loads during replanning instead of full reviews. Run `python .harness/scripts/compile_literature_summary.py --project <project-dir>` after adding or updating a review to regenerate `literature/summary.md`; prefer loading `summary.md` for routine replanning and load a full review only when a specific paper needs deeper inspection.
5. **Novelty map**: compare the planned contribution against reviewed papers and mark novelty as supported, weak, contradicted, or unverified.
6. **Reproduction target selection**: choose the smallest paper result, figure, equation, dataset, or benchmark that should be reproduced before new work.
7. **Replanning memo**: revise the research plan, validation gates, baselines, observables, and claim ceiling based on the literature.
8. **Researcher review checkpoint**: ask the researcher to inspect the paper set, novelty map, reproduction target, and revised plan before execution.

## Paper Request Rules

Before asking the researcher for any paper, the Lead Agent must first attempt web discovery:

1. **Web search first**: use the WebSearch tool (arXiv, Semantic Scholar, Google Scholar, publisher sites) to identify the exact title, authors, year, venue, and DOI or arXiv ID for each paper in the needed category.
2. **Check open access**: if a paper has an arXiv preprint or is available on PubMed Central or an open-access journal, fetch it directly using WebFetch. Do not request it from the researcher.
3. **Escalate only what is paywalled**: only add papers to `docs/literature/paper_request_queue.md` when they cannot be retrieved without institutional access. The queue entry must include the confirmed title, authors, year, DOI or arXiv ID, and the reason direct access failed — never a vague category like "a paper about X probably exists."
4. **No unverified requests**: do not ask the researcher to find a paper whose title or authors are unknown. If a web search cannot identify the paper, record it as an open literature question in `docs/literature/replanning_memo.md` instead.

Paper categories to cover:

- Foundational model or method papers
- Closest competing results
- Known benchmark or reproduction targets
- Review articles that map terminology and established baselines
- Recent papers likely to affect novelty
- Papers that contain figures, datasets, equations, or parameter regimes the project plans to compare against

If PDFs are missing after web search, mark the literature evidence as `missing` or `pending_review`; do not replace unavailable papers with unsupported summaries.

## Required Artifacts

Maintain a single project-local literature directory:

- `literature/pdfs/`: researcher-provided PDFs
- `literature/reviews/`: detailed paper review notes
- `literature/extracted_text/`: extracted PDF text used as a reading aid
- `literature/index.md`: project-local paper review index
- `docs/literature/paper_request_queue.md`: papers requested from the researcher
- `docs/literature/literature_review_plan.md`: current paper set, review status, and reading priorities
- `docs/literature/replanning_memo.md`: novelty map, reproduction target, revised plan, and claim ceiling

Repository templates live in `docs/literature/`.

For the literature helper script catalog (`scaffold_paper_review.py`, `extract_paper_text.py`, `draft_paper_review.py`, `process_paper_for_review.py`, `check_paper_review_quality.py` plus link-graph rules), the Review Agent rubric (max 5 parallel agents, review-log table with 판정/비고 columns, M1–M7 criteria), and the 18-item Detailed Review Standard (including the 확인 필요/unverified marking rule), see `skills/literature-review-planning/reference.md`.

## Output Format

Write the following sections into `docs/literature/literature_review_plan.md`.
The `## Literature Gate Status` section **must** be at level 2 (`##`) with
that exact name and must contain the word `ready` or `waived` —
`check_literature_reviewed.py` matches the heading level- and case-sensitively
and scans for those tokens. A `###`-level heading or any other name will
cause the gate to fail.

```markdown
## Paper Requests

<exact paper categories or known papers the researcher should collect as PDFs>

## Reviewed Evidence

<separate direct PDF evidence from external memory, abstracts, or unverified claims>

## Novelty Map

<what appears new, what is already known, what is contradicted, what is unverified>

## Reproduction Target

<smallest result that should be reproduced and why it is sufficient for the next gate>

## Revised Research Plan

<what changed in assumptions, observables, baselines, validation, and claim ceiling>

## Literature Gate Status

<one of: `ready` (review complete and plan revised) or `waived` (with explicit reason)>
```

The Literature Gate (`python .harness/scripts/check_literature_reviewed.py --project <project-dir>`) checks the `## Literature Gate Status` section before model-specification or seed-design work begins.

## Lineage Front-Matter

Each paper review file (and the reproduction-target / novelty-map decision) carries a `lineage:` block so `/sync-workflow` can seed `lineage_kind="paper"` nodes and `cites_paper` edges. For the full block format and rules, see `skills/literature-review-planning/reference.md`. Run `/sync-workflow` after adding or updating review files.

## Suggested Next Skill

**`model-specification`** — to define the physical model, variables, equations, and approximation regime informed by the literature review.
