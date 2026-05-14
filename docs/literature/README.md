# Literature Review Workspace

This directory holds repository-level templates for the literature replanning loop. Run-local literature artifacts should live in each run directory created by `scripts/start_research_run.py`.

## Purpose

Use this workspace before full research execution when literature access, novelty, or reproduction targets matter. The Professor Orchestrator requests PDFs from the researcher because the LLM may not have access to paywalled papers, institutional subscriptions, or local library holdings.

## Run-Local Layout

- `literature/pdfs/`: PDFs supplied by the researcher.
- `docs/paper_request_queue.md`: papers or paper categories requested from the researcher.
- `docs/literature_review_plan.md`: intake table and reading priorities.
- `docs/replanning_memo.md`: novelty map, reproduction target, revised plan, and claim ceiling.

## Discipline

- Do not infer novelty from memory alone.
- Distinguish direct PDF evidence from abstracts, metadata, and unverified summaries.
- Choose at least one reproduction target before claiming a project is ready for full execution, unless the researcher explicitly waives the gate.
- Keep unsupported novelty claims marked as unverified.

