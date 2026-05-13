# Docs Shallow Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize support documents under `docs/` into shallow folders while preserving active root checkpoints.

**Architecture:** Keep workflow and active research-control files in `docs/` root. Move adoption, harness-evaluation, and lower-frequency logs into dedicated subfolders, then update references in scripts, tests, generated workflow data, and instructions.

**Tech Stack:** Markdown, Python scripts, pytest, PowerShell file operations.

---

## File Structure

- Create: `docs/README.md`
- Create folders: `docs/adoption/`, `docs/harness/`, `docs/logs/`
- Move adoption docs into `docs/adoption/`
- Move harness evaluation docs into `docs/harness/`
- Move support logs into `docs/logs/`
- Modify references in `AGENTS.md`, `GEMINI.md`, `README.md`, `scripts/`, `tests/`, and affected docs.

## Tasks

### Task 1: Add Root Docs Index

**Files:**
- Create: `docs/README.md`

- [x] Add a concise map of root files and subfolders.

### Task 2: Move Support Documents

**Files:**
- Move adoption support docs from `docs/` root into `docs/adoption/`.
- Move harness evaluation support docs from `docs/` root into `docs/harness/`.
- Move anomaly, hypothesis, negative-result, open-question, reproduction, tacit-pattern, and toy-model logs from `docs/` root into `docs/logs/`.

- [x] Create folders and move files without changing file contents.

### Task 3: Update References

**Files:**
- Modify: `AGENTS.md`
- Modify: `GEMINI.md`
- Modify: `README.md`
- Modify: `scripts/audit_existing_project.py`
- Modify: `scripts/evaluate_harness.py`
- Modify: `scripts/run_baseline_validation.py`
- Modify: `tests/test_evaluate_harness.py`
- Modify: `docs/workflow_map.json`
- Modify: `docs/workflow_code_map.md`
- Modify: `docs/workflow_overview.md`
- Modify: moved harness and template docs as needed.

- [x] Replace moved paths with their new locations.

### Task 4: Validate

**Commands:**

```powershell
python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py -q
python scripts/evaluate_harness.py
python scripts/validate_workflow_links.py
```

- [x] Fix any stale path references found by tests or validation.
