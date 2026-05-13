# Run Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lightweight run templates for live workflow cartography and professor-led research run reporting.

**Architecture:** Add two Markdown templates under `docs/run_templates/`, then connect them to workflow documentation, the workflow code map, harness scenarios, and evaluator checks. Keep interview notes and user reporting inside one run packet to avoid duplicate paperwork.

**Tech Stack:** Markdown documentation, Python dataclass-based evaluator, pytest.

---

## File Structure

- Create `docs/run_templates/live_workflow_diagram_template.md`: Cartographer-owned live workflow template.
- Create `docs/run_templates/research_run_packet_template.md`: Professor-owned packet covering Interview, Seed, Execute, Evaluate, Completion Conference, User Report, and Retrospective.
- Modify `docs/workflow_overview.md`: mention the templates in live tracking and completion conference sections.
- Modify `docs/workflow_code_map.md`: map workflow visualization and retrospective/review areas to the templates.
- Modify `docs/harness_evaluation_scenarios.md`: add templates to expected docs for live workflow and completion conference scenarios.
- Modify `scripts/evaluate_harness.py`: add templates to scenario docs.
- Modify `tests/test_evaluate_harness.py`: assert evaluator scenarios require the templates.

## Tasks

### Task 1: Test Evaluator Template Coverage

- [ ] Add assertions that `live_workflow_diagram_agent` requires `docs/run_templates/live_workflow_diagram_template.md`.
- [ ] Add assertions that `completion_conference_reporting` requires `docs/run_templates/research_run_packet_template.md`.
- [ ] Run `python -m pytest tests/test_evaluate_harness.py -q` and expect failure before evaluator updates.

### Task 2: Add Templates

- [ ] Create `docs/run_templates/live_workflow_diagram_template.md`.
- [ ] Create `docs/run_templates/research_run_packet_template.md`.
- [ ] Keep the templates lightweight and explicit about supported versus unsupported claims.

### Task 3: Link Templates in Docs and Evaluator

- [ ] Update `docs/workflow_overview.md`.
- [ ] Update `docs/workflow_code_map.md`.
- [ ] Update `docs/harness_evaluation_scenarios.md`.
- [ ] Update `scripts/evaluate_harness.py`.

### Task 4: Validate

- [ ] Run `Compare-Object (Get-Content AGENTS.md) (Get-Content GEMINI.md)`.
- [ ] Run `rg -n "plt\\.show\\(" -g "*.py" -g "*.ipynb"`.
- [ ] Run `python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py -q`.
- [ ] Run `python scripts/evaluate_harness.py`.
