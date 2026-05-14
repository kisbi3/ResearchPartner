# Literature Replanning Loop Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Files:**
- Create: `skills/literature-review-planning/SKILL.md`
- Create: `docs/literature/README.md`
- Create: `docs/literature/paper_request_queue.md`
- Create: `docs/literature/literature_review_template.md`
- Create: `docs/literature/replanning_memo_template.md`
- Modify: `AGENTS.md`
- Modify: `GEMINI.md`
- Modify: `docs/run_templates/research_run_packet_template.md`
- Modify: `docs/run_templates/live_workflow_diagram_template.md`
- Modify: `scripts/start_research_run.py`
- Modify: `scripts/evaluate_harness.py`
- Modify: `tests/test_start_research_run.py`
- Modify: `tests/test_evaluate_harness.py`

- [x] **Step 1: Write failing tests**
  - Update run-scaffolder tests to require a run-local `literature/` directory and literature planning docs.
  - Update harness-evaluator tests to require a literature replanning scenario and the new skill.

- [x] **Step 2: Run targeted tests and confirm failure**
  - Run `python -m pytest tests/test_start_research_run.py tests/test_evaluate_harness.py`.
  - Expected failure: missing literature templates, missing scenario, and old scenario count.

- [x] **Step 3: Implement literature review planning workflow**
  - Add a dedicated skill that requires professor-led paper requests, researcher-provided PDFs, paper-by-paper review, novelty mapping, reproduction target selection, and iterative replanning before full research execution.
  - Add repository-level literature templates and run-local scaffolding.

- [x] **Step 4: Wire the harness rules**
  - Add AGENTS/GEMINI instructions in identical text.
  - Extend run packet and live workflow templates with the literature gate.
  - Extend harness evaluation scenarios.

- [x] **Step 5: Verify**
  - Run targeted tests.
  - Run `python scripts/evaluate_harness.py`.
  - Confirm `AGENTS.md` and `GEMINI.md` remain synchronized.
