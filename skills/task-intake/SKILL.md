---
name: task-intake
description: Use at the start of every research task to classify the work type, assign research roles, and surface the first professor question before any execution begins. This is the Orient phase.
---

# Task Intake Skill

Use this skill at the very beginning of any research task — before any other skill, implementation, or interpretation.

## Goal

Classify the research task, assign the responsible research role, and surface the first professor question. This is the Orient phase: do not execute, implement, or interpret until classification and the first question are complete.

## Task Classification

Classify the task as one or more of:

1. **New model** — defining or substantially changing a physical model, variables, equations, assumptions, or validity regime
2. **Existing project onboarding** — adding harness discipline to a project that already has code, data, figures, results, or claims
3. **Simulation** — running, modifying, or interpreting a numerical simulation or solver
4. **Analysis** — processing data, fitting, extracting observables, or reducing output
5. **Figure** — generating, auditing, or reinterpreting a figure or table
6. **Manuscript claim** — writing, strengthening, editing, or reviewing a claim, caption, abstract, or conclusion
7. **Anomaly / bug** — investigating a surprising, unstable, contradictory, or failed result
8. **Literature** — reading, reviewing, building a novelty map, or choosing reproduction targets from prior work
9. **Reproduction** — reproducing a published or prior result as a validation target
10. **Maintenance** — refactoring, cleaning, or reorganizing code, logs, or documents without changing scientific meaning
11. **Harness evaluation** — checking whether the harness itself is followed, useful, or light enough

A task may span multiple categories. List all that apply.

## Role Assignment

Assign the primary responsible role based on the task type:

| Task type | Primary role |
|---|---|
| New model, Manuscript claim, Literature, Reproduction | Lead Agent |
| Simulation, Analysis, Figure (first pass) | Lead Agent → Graduate Student → Implementation Agent + Scientific Validator + Cache-Log Auditor |
| Anomaly / bug | Lead Agent (classification) → Graduate Student → Implementation Agent (reproduction) |
| Existing project onboarding | Lead Agent (inventory) → Graduate Student (retrofit plan) |
| Maintenance, Harness evaluation | Lead Agent + `harness-evaluation` skill (no code changes), or Graduate Student → Implementation Agent (if files must be edited) |
| Workflow state update | Cartographer (hook-driven, not spawned) via `cartographer-update` skill |

If any part of the task involves a new claim, a baseline gate, or a gate waiver, the Lead Agent must be active.

## First Professor Question

Before any execution, state the single most important clarifying question. Choose one that surfaces the most uncertain or unstated assumption:

- What physical object or system is being studied?
- What observable is the research question about?
- What assumption is currently most uncertain?
- What failure criterion would invalidate the interpretation?
- What evidence would be needed to support the planned claim?
- Who decides when the result is good enough to report?

Ask only one question. Wait for the researcher's answer before proceeding to Interview or Specify.

## Gate Rule

Do not proceed to Interview, Specify, Seed, Validate, or Execute before:

1. The task is classified.
2. The responsible role is identified.
3. The first professor question is asked and answered.

If the task scope is unclear, classify what is known, mark uncertain categories as **unclear**, and ask the first professor question about the unclear scope.

## Orient Note

If the project is already initialized (a `.research-harness` marker exists at
the project root), write the output below into `docs/orient_note.md` at the
project root. This file is the artifact checked by
`scripts/check_orient_recorded.py` before Seed, Execute, or Evaluate work
may begin.

If the project is not yet initialized, remind the researcher to run
`python scripts/init_research_project.py` so the orient note
can be recorded before execution starts.

## Output Format

### Task Type

List all applicable categories.

### Responsible Role

Name the primary role and any supporting roles.

### Scope Note

One sentence describing the task and what makes it scientifically non-trivial.

### First Professor Question

The single most important clarifying question before execution begins.

### Suggested Next Skill

For most new research tasks, the next skill is `professor-interview`. This is the brainstorming dialogue that crystallizes the research question before Specify, Seed, or literature work begins.

Use `professor-interview` when the task is: New model, Simulation, Analysis, Figure, Manuscript claim, Literature, Reproduction, or Anomaly / bug.

Use a different next skill only in these cases:

- `existing-research-onboarding` — Existing project onboarding tasks
- `harness-evaluation` — Harness evaluation or Maintenance tasks
- `anomaly-debugging` — when an anomaly requires immediate reproduction before the research question can be crystallized
- `seed-design` — when the task is already fully specified and only needs a concrete task list (rare at Orient phase)
