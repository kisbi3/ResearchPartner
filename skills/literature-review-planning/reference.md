# Literature Review Planning — Reference

This is the reference companion to `skills/literature-review-planning/SKILL.md`. It holds the long-form material moved out of the skill body: the literature-helper script catalog, the Review Agent rubric, the 18-item Detailed Review Standard, and the lineage front-matter spec. Load it when you need the detail; SKILL.md keeps the durable workflow loop and the gate/waiver rule resident.

## Literature Helper Scripts

Use `.harness/scripts/scaffold_paper_review.py` to initialize a detailed review note and append it to `literature/index.md` when a paper enters the review set.

Use `.harness/scripts/extract_paper_text.py` to create an extracted-text artifact and link it from the review note. PDF text extraction is a reading aid, not evidence by itself; verify equations, figures, captions, tables, and claims against the PDF.

Use `.harness/scripts/draft_paper_review.py` only to insert a `Machine-Assisted Draft From Extracted Text` section with provisional candidates. This does not establish novelty or validate claims; the Lead Agent must require human/PDF verification before any candidate text affects the replanning memo.

Use `.harness/scripts/process_paper_for_review.py` when the PDF is already inside the project and the researcher wants the standard scaffold, extracted-text artifact, and provisional draft in one step.

Maintain clickable links across the literature graph. The paper index should link to PDFs and review notes, each review note should link to the paper index and replanning memo, and extracted text artifacts should link back to the source PDF and review note. Keep project-relative code paths alongside Markdown links so future agents can inspect artifacts without guessing locations.

Run `.harness/scripts/check_paper_review_quality.py` on important review notes before using them to update `docs/literature/replanning_memo.md`. If the check fails, either complete the review or record an explicit waiver and keep novelty/reproduction claims provisional.

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

## Lineage Front-Matter

Each paper review file you write to `literature/reviews/<paper_id>.md` is picked up by `/sync-workflow`, which seeds a `lineage_kind="paper"` node. Add a `lineage:` block at the top of each review file to record key relations:

```yaml
---
lineage:
  node_type: paper
  lineage_kind: paper
  paper_id: smith2020               # must match the filename stem
---
```

For the **reproduction target selection** and **novelty map result**, add corresponding `lineage:` blocks to `docs/literature/replanning_memo.md` (or a separate decision file) with `cites_paper` edges to the papers they rely on.

Run `/sync-workflow` after adding or updating review files to update the live workflow map. See `skills/sync-workflow/SKILL.md` for the full front-matter spec.
