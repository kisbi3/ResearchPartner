# Run Scaffolder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a command-line scaffolder that creates a new research run from the live workflow and research run packet templates.

**Architecture:** A focused Python script owns slugging, run directory creation, template copying, and minimal log initialization. Tests import the script module directly and exercise it against a temporary runs root.

**Tech Stack:** Python standard library, pytest, Markdown templates.

---

## File Structure

- Create `scripts/start_research_run.py`: command-line scaffolder and testable helper functions.
- Create `tests/test_start_research_run.py`: TDD coverage for creation, duplicate protection, and slug behavior.
- Modify `docs/workflow_overview.md`: mention the start command.
- Modify `docs/workflow_code_map.md`: map the scaffolder to workflow visualization/run setup.
- Modify `scripts/evaluate_harness.py`: require the scaffolder in the live workflow scenario.

## Tasks

### Task 1: Scaffolder Tests

- [x] Write failing tests that import `scripts/start_research_run.py`.
- [x] Assert a run root contains `docs/live_workflow_diagram.md`, `research_run_packet.md`, expected docs, and `outputs/`.
- [x] Assert duplicate runs raise `FileExistsError`.
- [x] Assert names slugify to lowercase hyphenated names.

### Task 2: Scaffolder Implementation

- [x] Implement `slugify_name`.
- [x] Implement `create_run`.
- [x] Implement CLI parsing with `--name`, `--date`, and `--runs-root`.
- [x] Refuse overwrite by default.

### Task 3: Documentation and Evaluation

- [x] Add the command to `docs/workflow_overview.md`.
- [x] Add `scripts/start_research_run.py` to `docs/workflow_code_map.md`.
- [x] Add `scripts/start_research_run.py` to the live workflow evaluator scenario.

### Task 4: Validation

- [x] Run `python -m pytest tests/test_start_research_run.py -q`.
- [x] Run `python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py tests/test_start_research_run.py -q`.
- [x] Run `python scripts/evaluate_harness.py`.
- [x] Run `python scripts/validate_workflow_links.py`.
- [x] Run `rg -n "plt\\.show\\(" -g "*.py" -g "*.ipynb"`.
