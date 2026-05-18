---
name: literature-review-planning
description: Use before full research execution when a project needs literature discovery, researcher-provided PDFs, novelty assessment, reproduction target selection, or PaperQA-style review.
---

# Literature Review Planning Skill

Use this skill between professor-interview and model-specification.

## Prerequisites

Before starting:

1. Confirm `docs/interview_notes.md` exists and the Interview Gate passes (`python scripts/check_interview_recorded.py --project <project-dir>`). If not, complete the professor-interview skill first.

## Skipping This Step

If the literature review is genuinely not needed for this iteration (e.g. reproducing a known result with well-understood prior work), the researcher may skip this step by creating `docs/literature_skip_waiver.md` with a one-line reason:

```
Skipping literature review: reproducing Fourier (1822) heat equation — prior work is fully known and no novelty is claimed.
```

The Literature Gate (`python scripts/check_literature_reviewed.py --project <project-dir>`) passes on either a completed review or a waiver file with content. A skip lowers the claim ceiling to at most `interpretation` for this iteration. The goal is not to let an LLM invent a literature review; the goal is to make the researcher's paper access and judgment part of the workflow before simulations, figures, or manuscript claims begin.

## Goal

Create an iterative literature replanning loop that turns paper requests, researcher-provided PDFs, direct paper review, novelty mapping, and reproduction target selection into a stronger second-stage research plan.

## Required Loop

Repeat this loop until the Lead Agent marks the plan ready or the researcher explicitly waives the literature gate:

1. **Question framing**: state the research question, physical system, observable, and candidate claim.
2. **Paper request**: ask the researcher to collect specific PDFs that the LLM cannot access directly, using institutional access when needed.
3. **Paper intake**: record each PDF path, citation metadata, access status, relevance, and whether it has been read.
4. **Direct review**: create one detailed review note per important paper in `literature/reviews/`. The note must be a section-by-section paper review, not a short abstract summary. It should reconstruct the paper's context, concepts, method, equations, assumptions, units, figures/tables, limitations, and reusable research value. Each review note must fill in the **`Context Summary`** block (between the `<!-- context-summary:start -->` and `<!-- context-summary:end -->` HTML markers) — this block is the compact form the Lead Agent loads during replanning instead of full reviews. Run `python scripts/compile_literature_summary.py --project <project-dir>` after adding or updating a review to regenerate `literature/summary.md`; prefer loading `summary.md` for routine replanning and load a full review only when a specific paper needs deeper inspection.
5. **Novelty map**: compare the planned contribution against reviewed papers and mark novelty as supported, weak, contradicted, or unverified.
6. **Reproduction target selection**: choose the smallest paper result, figure, equation, dataset, or benchmark that should be reproduced before new work.
7. **Replanning memo**: revise the research plan, validation gates, baselines, observables, and claim ceiling based on the literature.
8. **Researcher review checkpoint**: ask the researcher to inspect the paper set, novelty map, reproduction target, and revised plan before execution.

## Paper Request Rules

Before asking the researcher for any paper, the Lead Agent must first attempt web discovery:

1. **Web search first**: use the WebSearch tool (arXiv, Semantic Scholar, Google Scholar, publisher sites) to identify the exact title, authors, year, venue, and DOI or arXiv ID for each paper in the needed category.
2. **Check open access**: if a paper has an arXiv preprint or is available on PubMed Central or an open-access journal, fetch it directly using WebFetch. Do not request it from the researcher.
3. **Escalate only what is paywalled**: only add papers to `docs/paper_request_queue.md` when they cannot be retrieved without institutional access. The queue entry must include the confirmed title, authors, year, DOI or arXiv ID, and the reason direct access failed — never a vague category like "a paper about X probably exists."
4. **No unverified requests**: do not ask the researcher to find a paper whose title or authors are unknown. If a web search cannot identify the paper, record it as an open literature question in `docs/replanning_memo.md` instead.

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
- `docs/paper_request_queue.md`: papers requested from the researcher
- `docs/literature_review_plan.md`: current paper set, review status, and reading priorities
- `docs/replanning_memo.md`: novelty map, reproduction target, revised plan, and claim ceiling

Repository templates live in `docs/literature/`.

Use `scripts/scaffold_paper_review.py` to initialize a detailed review note and append it to `literature/index.md` when a paper enters the review set.

Use `scripts/extract_paper_text.py` to create an extracted-text artifact and link it from the review note. PDF text extraction is a reading aid, not evidence by itself; verify equations, figures, captions, tables, and claims against the PDF.

Use `scripts/draft_paper_review.py` only to insert a `Machine-Assisted Draft From Extracted Text` section with provisional candidates. This does not establish novelty or validate claims; the Lead Agent must require human/PDF verification before any candidate text affects the replanning memo.

Use `scripts/process_paper_for_review.py` when the PDF is already inside the project and the researcher wants the standard scaffold, extracted-text artifact, and provisional draft in one step.

Maintain clickable links across the literature graph. The paper index should link to PDFs and review notes, each review note should link to the paper index and replanning memo, and extracted text artifacts should link back to the source PDF and review note. Keep project-relative code paths alongside Markdown links so future agents can inspect artifacts without guessing locations.

Run `scripts/check_paper_review_quality.py` on important review notes before using them to update `docs/replanning_memo.md`. If the check fails, either complete the review or record an explicit waiver and keep novelty/reproduction claims provisional.

## Review Agent Rules

When running graduate-student agents to write paper reviews in parallel:

- **Maximum 5 agents in one parallel batch** — never exceed this limit to avoid usage-rate failures.
- **Read template via tool**: the grad-student agent must read `docs/process/review_template.md` using the Read tool before writing. Do not paste the template inline in the spawn prompt — the prompt would grow too large and the agent would use a stale copy.
- **Professor evaluation tracking**: after each professor evaluation (pass or fail), record the result immediately in `docs/process/researcher_review_log.md` using this table format:

  | Date | Paper ID | M1 | M2 | M3 | M4 | M5 | M6 | M7 | 판정 | 비고 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | YYYY-MM-DD | XX | ✓/✗/– | … | … | … | … | … | … | PASS/FAIL | notes |

  M1–M7 are the mandatory rubric criteria from `docs/process/review_rubric.md`. Every evaluation must appear in this log, including inline evaluations done in the main context.

## Detailed Review Standard

Each important paper review should be reusable by a future researcher. Include:

- metadata and PDF path
- executive summary and project relevance
- research context, motivation, and the paper's question
- key concepts and definitions
- data, simulation, model, or experimental construction
- proposed method and comparison methods
- metrics, validation, equations, assumptions, units, parameters, and approximation regime
- Figure/Table-by-Figure/Table Review
- results logic and what the evidence actually establishes
- discussion, limitations, overclaim risks, and links to prior literature
- connection to the current project
- reproduction extraction with pass/fail criteria
- novelty and claim impact
- dictionary or internal note candidates
- final takeaway and citation cautions

Separate the authors' claims from the reviewer interpretation and from the project's planned claims. Mark uncertain statements as `확인 필요` or `unverified`.

## Output Format

### Literature Gate Status

Ready / needs PDFs / needs review / needs reproduction target / needs novelty revision / waived.

### Paper Requests

List the exact paper categories or known papers the researcher should collect as PDFs.

### Reviewed Evidence

Separate direct PDF evidence from external memory, abstracts, or unverified claims.

### Novelty Map

State what appears new, what is already known, what is contradicted, and what is unverified.

### Reproduction Target

Name the smallest result that should be reproduced and why it is sufficient for the next gate.

### Revised Research Plan

State what changed in assumptions, observables, baselines, validation, and claim ceiling.

### Literature Gate Status

Set this to one of: `ready` (review complete and plan revised) or `waived` (with explicit reason). Write this section into `docs/literature_review_plan.md` at the project root. The Literature Gate (`python scripts/check_literature_reviewed.py --project <project-dir>`) checks this section before model-specification or seed-design work begins.

## Cartographer Update

Each paper review file you write to `literature/reviews/<paper_id>.md` is auto-detected by `scripts/workflow_hooks.py`, which seeds a `lineage_kind="paper"` node with `paper_id=<filename stem>` in `workflow_map.live.json`. You do not need to emit the paper node yourself.

You **must** explicitly emit:

- a `decision` node for the **reproduction target selection** with a `cites_paper` edge to each chosen paper, and
- a `decision` node for the **novelty map result** with `cites_paper` edges to the papers it relied on.

See worked examples in `skills/cartographer-update/SKILL.md` → *Worked Examples by Lineage Kind* → "Paper node + cites_paper edge". Use `paper_<paper_id>` as the target `node_id` to match the auto-emitted paper node.

## Suggested Next Skill

**`model-specification`** — to define the physical model, variables, equations, and approximation regime informed by the literature review.
