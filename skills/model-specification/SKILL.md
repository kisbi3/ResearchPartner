---
name: model-specification
description: Use when defining, reviewing, modifying, or documenting a physical model, its variables, assumptions, equations, parameters, constraints, or validity regime.
---

# Model Specification Skill

Use this skill after literature-review-planning completes (or is waived).

## Prerequisites

Before starting:

1. Confirm the Literature Gate passes: `python .harness/scripts/check_literature_reviewed.py --project <project-dir>`. If not, either complete the literature-review-planning skill or create `docs/literature/literature_skip_waiver.md` with a one-line reason.

## Skipping This Step

If the model is already fully specified from prior work (e.g. continuing an existing project with no model changes), the researcher may skip this step by creating `docs/plan/model_skip_waiver.md` with a one-line reason:

```
Skipping model specification: continuing prior work — model unchanged from docs/plan/model_spec.md dated 2026-05-10.
```

The Model Gate (`python .harness/scripts/check_model_specified.py --project <project-dir>`) passes on either a completed model_spec.md or a waiver file with content. A skip lowers the claim ceiling to at most `observation` for this iteration.

## Artifact

Write the model specification output into `docs/plan/model_spec.md` at the project root. This file is the gate artifact checked by `.harness/scripts/check_model_specified.py`. Use the template at `docs/run_templates/model_spec_template.md` as the starting structure.

## Goal

Make the model explicit enough that another researcher can reproduce and critique it.

## Required Model Components

1. Physical system
2. Degrees of freedom
3. State variables
4. Governing equations
5. Parameters
6. Units
7. Initial conditions
8. Boundary conditions
9. Constraints
10. Symmetries
11. Conservation laws
12. Approximation regime
13. Observables
14. Numerical or analytical method

## Model Specification Template

Write the following template into `docs/plan/model_spec.md`. The headings
**must** be level 2 (`##`) with the exact names shown — `check_model_specified.py`
requires both `## Physical System` and `## Governing Equations` at level 2.
Using `###` or renaming the headings will cause the Model Gate to fail.

```markdown
## Physical System

<describe the system being modeled>

## Degrees of Freedom

<list the variables that define the system state>

## Governing Equations

<write the equations and define every symbol>

## Assumptions

<list all assumptions explicitly>

## Parameters

| Parameter | Meaning | Units | Default / Range |
|---|---|---|---|

## Initial Conditions

<specify initial state or ensemble>

## Boundary Conditions

<specify boundary behavior>

## Observables

<list measured or computed outputs>

## Validity Regime

<state when the model is expected to hold>

## Known Limitations

<state what the model excludes>

## Model Gate Status

<set to `ready` when all required components above are filled>
```

The Model Gate (`python .harness/scripts/check_model_specified.py --project <project-dir>`) checks this file before seed-design or execute work begins. The canonical template lives at `docs/run_templates/model_spec_template.md`.

## Lineage Front-Matter

When this skill produces a new model definition (or a revised version of an existing model), also write a one-page model-version note to `docs/model_versions/<version>.md` (e.g. `v1.md`). Add a `lineage:` block at the top of that file to record lineage edges:

```yaml
---
lineage:
  node_type: model_version
  model_version: "v1"
  evolved_from: model_v0          # omit if this is the first version
  cites_paper:
    - paper_smith2020             # each paper whose equations/method the spec relies on
---
```

Then run `/sync-workflow` to pick up the new file and update the live workflow map. See `skills/sync-workflow/SKILL.md` for the full front-matter spec and supported relations.

## Suggested Next Skill

**`baseline-strategy`** — professor-graduate student dialogue to decide whether the model is a variation (requiring reproduction) or a new model (requiring analytical limit verification), and to fix the first verification target before seed-design begins.
