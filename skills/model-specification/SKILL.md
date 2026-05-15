---
name: model-specification
description: Use when defining, reviewing, modifying, or documenting a physical model, its variables, assumptions, equations, parameters, constraints, or validity regime.
---

# Model Specification Skill

Use this skill after literature-review-planning completes (or is waived).

## Prerequisites

Before starting:

1. Confirm the Literature Gate passes: `python scripts/check_literature_reviewed.py --run <run-dir>`. If not, either complete the literature-review-planning skill or create `docs/literature_skip_waiver.md` with a one-line reason.

## Skipping This Step

If the model is already fully specified from prior work (e.g. continuing an existing run with no model changes), the researcher may skip this step by creating `docs/model_skip_waiver.md` with a one-line reason:

```
Skipping model specification: continuing prior run — model unchanged from docs/model_spec.md dated 2026-05-10.
```

The Model Gate (`python scripts/check_model_specified.py --run <run-dir>`) passes on either a completed model_spec.md or a waiver file with content. A skip lowers the claim ceiling to at most `observation` for this run.

## Artifact

Write the model specification output into `docs/model_spec.md` in the run directory. This file is the gate artifact checked by `scripts/check_model_specified.py`. Use the template at `docs/run_templates/model_spec_template.md` as the starting structure.

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

### Physical System

Describe the system being modeled.

### Degrees of Freedom

List the variables that define the system state.

### Governing Equations

Write the equations and define every symbol.

### Assumptions

List all assumptions explicitly.

### Parameters

| Parameter | Meaning | Units | Default / Range |
|---|---|---|---|

### Initial Conditions

Specify initial state or ensemble.

### Boundary Conditions

Specify boundary behavior.

### Observables

List measured or computed outputs.

### Validity Regime

State when the model is expected to hold.

### Known Limitations

State what the model excludes.

### Model Gate Status

Set to `ready` when all required components above are filled in `docs/model_spec.md`. The Model Gate (`python scripts/check_model_specified.py --run <run-dir>`) checks this file before seed-design or execute work begins.

## Suggested Next Skill

**`seed-design`** — to convert the specified model into concrete, bounded graduate-agent tasks.
