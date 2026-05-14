---
name: literature-review-planning
description: Use before full research execution when a project needs literature discovery, researcher-provided PDFs, novelty assessment, reproduction target selection, or PaperQA-style review.
---

# Literature Review Planning Skill

Use this skill between initial research planning and full execution. The goal is not to let an LLM invent a literature review; the goal is to make the researcher's paper access and judgment part of the workflow before simulations, figures, or manuscript claims begin.

## Goal

Create an iterative literature replanning loop that turns paper requests, researcher-provided PDFs, direct paper review, novelty mapping, and reproduction target selection into a stronger second-stage research plan.

## Required Loop

Repeat this loop until the Professor Orchestrator marks the plan ready or the researcher explicitly waives the literature gate:

1. **Question framing**: state the research question, physical system, observable, and candidate claim.
2. **Paper request**: ask the researcher to collect specific PDFs that the LLM cannot access directly, using institutional access when needed.
3. **Paper intake**: record each PDF path, citation metadata, access status, relevance, and whether it has been read.
4. **Direct review**: create one detailed review note per important paper in `literature/reviews/`. The note must be a section-by-section paper review, not a short abstract summary. It should reconstruct the paper's context, concepts, method, equations, assumptions, units, figures/tables, limitations, and reusable research value.
5. **Novelty map**: compare the planned contribution against reviewed papers and mark novelty as supported, weak, contradicted, or unverified.
6. **Reproduction target selection**: choose the smallest paper result, figure, equation, dataset, or benchmark that should be reproduced before new work.
7. **Replanning memo**: revise the research plan, validation gates, baselines, observables, and claim ceiling based on the literature.
8. **Researcher review checkpoint**: ask the researcher to inspect the paper set, novelty map, reproduction target, and revised plan before execution.

## Paper Request Rules

The Professor Orchestrator should request papers by category rather than guessing that the current set is complete:

- Foundational model or method papers
- Closest competing results
- Known benchmark or reproduction targets
- Review articles that map terminology and established baselines
- Recent papers likely to affect novelty
- Papers that contain figures, datasets, equations, or parameter regimes the project plans to compare against

If PDFs are missing, mark the literature evidence as `missing` or `pending_review`; do not replace unavailable papers with unsupported summaries.

## Required Artifacts

Maintain a single run-local literature directory:

- `literature/pdfs/`: researcher-provided PDFs
- `literature/reviews/`: detailed paper review notes
- `literature/extracted_text/`: extracted PDF text used as a reading aid
- `literature/index.md`: run-local paper review index
- `docs/paper_request_queue.md`: papers requested from the researcher
- `docs/literature_review_plan.md`: current paper set, review status, and reading priorities
- `docs/replanning_memo.md`: novelty map, reproduction target, revised plan, and claim ceiling

Repository templates live in `docs/literature/`.

Use `scripts/scaffold_paper_review.py` to initialize a detailed review note and append it to `literature/index.md` when a paper enters the review set.

Use `scripts/extract_paper_text.py` to create an extracted-text artifact and link it from the review note. PDF text extraction is a reading aid, not evidence by itself; verify equations, figures, captions, tables, and claims against the PDF.

Use `scripts/draft_paper_review.py` only to insert a `Machine-Assisted Draft From Extracted Text` section with provisional candidates. This does not establish novelty or validate claims; the Professor Orchestrator must require human/PDF verification before any candidate text affects the replanning memo.

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
