# Literature Review Workspace

This directory holds repository-level templates for the literature replanning loop. Run-local literature artifacts should live in each run directory created by `scripts/start_research_run.py`.

## Purpose

Use this workspace before full research execution when literature access, novelty, or reproduction targets matter. The Lead Agent requests PDFs from the researcher because the LLM may not have access to paywalled papers, institutional subscriptions, or local library holdings.

## Run-Local Layout

- `literature/pdfs/`: PDFs supplied by the researcher.
- `literature/reviews/`: detailed, reusable, section-by-section paper review notes.
- `literature/extracted_text/`: extracted PDF text used as a reading aid.
- `literature/index.md`: run-local index of requested, received, reviewed, deferred, and rejected papers.
- `docs/paper_request_queue.md`: papers or paper categories requested from the researcher.
- `docs/literature_review_plan.md`: intake table and reading priorities.
- `docs/replanning_memo.md`: novelty map, reproduction target, revised plan, and claim ceiling.

## Review Note Scaffolding

Use `python scripts/scaffold_paper_review.py --run <run-dir> --paper-id P1 --title "<paper title>" --pdf <run-dir>/literature/pdfs/<paper>.pdf --role benchmark` to create a detailed review note and append it to the run-local paper index.

Use `python scripts/extract_paper_text.py --run <run-dir> --paper-id P1 --pdf <run-dir>/literature/pdfs/<paper>.pdf --review <run-dir>/literature/reviews/<review>.md` to save extracted PDF text and link it from the review note.

Use `python scripts/draft_paper_review.py --review <run-dir>/literature/reviews/<review>.md --extracted-text <run-dir>/literature/extracted_text/<paper>.txt` to insert a `Machine-Assisted Draft From Extracted Text` section. Treat this as a provisional reading aid only.

Use `python scripts/process_paper_for_review.py --run <run-dir> --paper-id P1 --title "<paper title>" --pdf <run-dir>/literature/pdfs/<paper>.pdf --role benchmark` to run scaffold, text extraction, and provisional drafting in one step.

Use `python scripts/check_paper_review_quality.py <run-dir>/literature/reviews/<review>.md` before promoting a review into `docs/replanning_memo.md`.

## Discipline

- Do not infer novelty from memory alone.
- Distinguish direct PDF evidence from abstracts, metadata, and unverified summaries.
- Keep the literature graph linked: `literature/index.md` should link to PDFs and review notes, review notes should link back to the index and replanning memo, and extracted text artifacts should link back to their source PDF and review note.
- PDF text extraction is a reading aid, not evidence by itself. Verify equations, captions, tables, and claims against the PDF.
- A machine-assisted draft from extracted text does not establish novelty or validate claims. It only creates candidates for human review.
- The literature investigation stage is complete only after important paper reviews pass `scripts/check_paper_review_quality.py` or the researcher records an explicit waiver in the replanning memo.
- Write detailed paper reviews, not short abstract summaries. A review should reconstruct context, methods, equations, figures/tables, limitations, reuse value, and reproduction details.
- Choose at least one reproduction target before claiming a project is ready for full execution, unless the researcher explicitly waives the gate.
- Keep unsupported novelty claims marked as unverified.
