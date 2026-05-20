---
name: task-intake
description: Use at the start of every research task to classify the work type, assign research roles, and surface the first professor question before any execution begins. This is the Orient phase.
---

# Task Intake Skill

Use this skill at the very beginning of any research task — before any other skill, implementation, or interpretation.

## Goal

Classify the research task, assign the responsible research role, and surface the first professor question. This is the Orient phase: do not execute, implement, or interpret until classification and the first question are complete.

## Project Initialization (Hard Gate, Runs First)

Before classifying the task, check whether the current working directory is a marked research project.

1. If a `.research-harness` marker file exists at the project root (cwd or any ancestor), proceed to Task Classification below.
2. If **no** marker is found, **automatically run** `python scripts/init_research_project.py` from cwd before asking the researcher anything. This is not optional and is not a question — the harness cannot record orient notes, gate artefacts, or lineage state without the project structure.

After init completes:

- A `.research-harness` marker is written at the project root.
- `docs/`, `literature/`, `src/`, `outputs/`, `cache/`, `logs/`, `errors/` are scaffolded.
- An empty `workflow_map.live.json` is bootstrapped.

Only then proceed to classification. Do NOT ask the researcher whether to initialize; do NOT show them the run-directory tree as a question. Initialization is a precondition, not a step they approve.

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
| Workflow state update | Lead Agent via `/sync-workflow` (on-demand, not spawned) |

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

Write the output below into `docs/gates/orient_note.md` (i.e.,
`<project-root>/docs/gates/orient_note.md`, where the project root is the
directory containing the `.research-harness` marker — created by the
Project Initialization step above if it did not already exist). This exact
path is what `scripts/check_orient_recorded.py` checks; writing to any
other location (e.g. `docs/orient_note.md` at the project root, without the
`gates/` subdirectory) will leave the Orient gate permanently Pending.

The file **must** use the four `##` section headings shown below, with those
exact names and level-2 (`##`) markers. `check_orient_recorded.py` matches
headings case-sensitively and level-sensitively; `###` or renamed headings
will cause a "sections are still blank" failure even when the content is
present.

## Output Format

Write the following template into `docs/gates/orient_note.md`, replacing the
placeholder text under each heading with real content:

```markdown
## Task Classification

<list all applicable categories from the Task Classification section above>

## Responsible Role

<primary role and any supporting roles>

## First Professor Question

<the single most important clarifying question before execution begins>

## Researcher Answer

<record the researcher's answer here after they reply; leave a placeholder
such as "Awaiting researcher answer." if the question has not yet been asked>
```

All four sections must be non-empty and must not contain only HTML comments
for the gate to pass. The `## Researcher Answer` section in particular is
often forgotten — fill it in as soon as the researcher responds, before any
Seed, Execute, or Evaluate work begins.

### Required Skill Order (No Short-Cuts)

For New model, Simulation, Analysis, Manuscript claim, or Reproduction tasks, the Lead Agent MUST traverse these skills in order before any code is written, any simulation is run, or any claim is drafted:

1. `task-intake` (this skill) — Orient
2. `professor-interview` — Interview
3. `literature-review-planning` — Literature (skip only via explicit `docs/literature/literature_skip_waiver.md`)
4. `model-specification` — Specify (skip only via explicit `docs/plan/model_skip_waiver.md`)
5. `baseline-strategy` — Decide variation vs new-model verification target (no skip waiver)
6. `seed-design` — Seed (concrete tasks)
7. `baseline-validation` — Validate baseline before full-scale execution

Skipping a step in this order is a workflow violation. The corresponding gate-check script will refuse downstream work:

- `scripts/check_interview_recorded.py` blocks Specify/Seed/Execute until `docs/gates/interview_notes.md` is filled.
- `scripts/check_literature_reviewed.py` blocks model-spec / seed-design until `docs/literature/literature_review_plan.md` is either `ready` or `waived`.
- `scripts/check_model_specified.py` blocks seed-design until `docs/plan/model_spec.md` is filled or waived.
- `scripts/check_baseline_strategy.py` blocks seed-design until `docs/plan/baseline_strategy.md` records a decision (no skip waiver).
- `scripts/check_baseline_gate.py` blocks Execute / Evaluate until a baseline result is recorded.

When the researcher seems eager to jump ahead ("just start coding", "skip the lit review"), do not comply. Either run the skipped skill, or surface the explicit waiver file with the reason and risk. Bypassing a gate without a waiver is a workflow violation that the Lead Agent must refuse.

## Suggested Next Skill

For most new research tasks, the next skill is `professor-interview`. This is the brainstorming dialogue that crystallizes the research question before Specify, Seed, or literature work begins.

Use `professor-interview` when the task is: New model, Simulation, Analysis, Figure, Manuscript claim, Literature, Reproduction, or Anomaly / bug.

Use a different next skill only in these cases:

- `existing-research-onboarding` — Existing project onboarding tasks
- `harness-evaluation` — Harness evaluation or Maintenance tasks
- `anomaly-debugging` — when an anomaly requires immediate reproduction before the research question can be crystallized
- `seed-design` — when the task is already fully specified and only needs a concrete task list (rare at Orient phase)
