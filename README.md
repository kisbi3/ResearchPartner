# Physics Research Harness

A lightweight harness for physics research workflows with AI assistants.

The goal is to make the assistant preserve scientific discipline across the whole chain:

physical question -> assumptions -> model -> equations -> dimensional check -> baseline validation -> numerical implementation -> validation -> researcher review -> figures -> manuscript claims.

## What This Harness Enforces

- Physical assumptions must be explicit.
- Equations and parameters should be dimensionally checked.
- New models, solvers, analysis pipelines, and figure workflows should pass a toy-model, known-limit, benchmark, or reproduction check before full-scale interpretation.
- Intermediate results should be shown to the researcher in reviewable iterations.
- Existing research projects can adopt the harness through a non-destructive intake and retrofit workflow.
- Figures and manuscript claims must be traceable to code, data, logs, derivations, or citations.
- `plt.show()` should not be used; save figures to files instead.

## Structure

```text
physics-research-harness/
├── AGENTS.md
├── GEMINI.md
├── PHYSICS.md
├── README.md
├── skills/
│   ├── baseline-validation/
│   ├── claim-to-evidence/
│   ├── dimensional-analysis/
│   ├── existing-research-onboarding/
│   ├── model-specification/
│   ├── numerical-validation/
│   └── researcher-review-loop/
├── docs/
│   ├── adoption_log.md
│   ├── assumptions.md
│   ├── baseline_registry.md
│   ├── decision_log.md
│   ├── existing_project_intake.md
│   ├── existing_results_inventory.md
│   ├── reproduction_log.md
│   ├── researcher_review_log.md
│   ├── retrofit_validation_plan.md
│   ├── toy_model_log.md
│   └── validation_log.md
└── scripts/
    ├── audit_existing_project.py
    └── run_baseline_validation.py
```

## Recommended Research Loop

1. Define the physical question and model.
2. Record assumptions in `docs/assumptions.md`.
3. Specify at least one baseline in `docs/baseline_registry.md`.
4. Validate with a toy model, analytical limit, reproduction target, conservation check, or dimensional sanity case.
5. Record validation in `docs/validation_log.md`, `docs/toy_model_log.md`, or `docs/reproduction_log.md`.
6. Present intermediate results using `skills/researcher-review-loop/SKILL.md`.
7. Record decisions in `docs/decision_log.md`.
8. Only then expand to full-scale runs, production figures, or manuscript-level claims.

## Core Skills

- `model-specification`: define physical systems, variables, equations, assumptions, parameters, and validity regimes.
- `dimensional-analysis`: check units, dimensions, nondimensionalization, and dimensionless groups.
- `baseline-validation`: require toy-model, known-limit, benchmark, or reproduction checks before trusting new workflows.
- `existing-research-onboarding`: attach the harness to already-running research without rewriting history or overvalidating old results.
- `numerical-validation`: check reproducibility, convergence, stability, conservation laws, and known limits.
- `claim-to-evidence`: map scientific claims to derivations, simulations, figures, data, tables, or citations.
- `researcher-review-loop`: package intermediate results for human scientific review and decision logging.

## Adding the Harness to Existing Research

When a project already has results, start with intake instead of cleanup.

1. Run a lightweight inventory:

```bash
python scripts/audit_existing_project.py path/to/project
```

2. Fill out `docs/existing_project_intake.md`.
3. Record prior outputs in `docs/existing_results_inventory.md`.
4. Mark validation status honestly as `validated`, `partial`, `unknown`, `failed`, `waived`, or `deprecated`.
5. Pick one first retrofit target in `docs/retrofit_validation_plan.md`.
6. Prefer reproducing one existing figure, checking one toy model, auditing one simulation pipeline, or mapping one manuscript section to evidence.

Do not reorganize or reinterpret old results before this intake is complete.

## Quick Check

Run:

```bash
python scripts/run_baseline_validation.py
```

This checks that the harness files exist and scans common code directories for direct `plt.show()` usage.

To audit an already-running research project:

```bash
python scripts/audit_existing_project.py path/to/project --output existing-project-audit.md
```

## Adapting to a Research Repository

Copy the harness files into a physics project:

```text
my-physics-project/
├── AGENTS.md
├── GEMINI.md
├── PHYSICS.md
├── skills/
├── docs/
├── src/
├── scripts/
├── data/
├── results/
└── manuscript/
```

Project-specific scientific questions belong in a separate project research note. General physics discipline belongs in `PHYSICS.md`.
