---
name: existing-research-onboarding
description: Use when attaching the physics research harness to an existing project with prior code, data, figures, simulations, notes, results, or manuscript claims.
---

# Existing Research Onboarding Skill

Use this skill when a research project is already in progress and the harness is being added after results, scripts, figures, notes, or manuscript text already exist.

## Goal

Attach the harness without rewriting history, hiding uncertainty, or forcing old work into a false validation story.

## Core Rule

Inventory first, interpret later.

Do not reorganize, rename, rewrite, rerun, or reinterpret existing artifacts until the current state is visible and the researcher has chosen the first retrofit target.

## Required Intake

Record:

1. Existing research question or working hypothesis
2. Main models or physical systems
3. Important scripts and notebooks
4. Existing data and generated outputs
5. Existing figures and tables
6. Manuscript, notes, slides, or reports
7. Known assumptions
8. Known failed runs or anomalies
9. Existing validation evidence
10. Unknown validation status

## Retrofit Status Labels

Use these labels consistently:

- `validated`: evidence is recorded and sufficient for the intended claim
- `partial`: some checks exist, but gaps remain
- `unknown`: artifact exists but validation has not been checked
- `failed`: check was run and did not pass
- `waived`: researcher explicitly accepted the risk
- `deprecated`: artifact should no longer support current claims

## First Retrofit Target

Choose one narrow target:

- reproduce one existing figure
- validate one toy model
- audit one simulation pipeline
- map one manuscript section to evidence
- check dimensions for one model
- rerun one benchmark or known limit

Avoid whole-project rewrites as the first step.

## Adoption Gate (how onboarding satisfies the gate chain)

The harness gate chain is greenfield-shaped — it normally expects a freshly
authored model spec and baseline strategy. An existing project already has both,
so onboarding uses the **adoption decision gate** instead of re-authoring them:

1. **Inventory first.** Run `python scripts/audit_existing_project.py <root>` and
   fill `docs/adoption/existing_project_intake.md`,
   `existing_results_inventory.md`, and `retrofit_validation_plan.md`. This is the
   lab's proposal — do not interpret or rerun yet.
2. **PI signs `docs/gates/adoption_decision.md`** (`## Decision`), recording the
   accepted existing model, the existing result chosen as the reproduction
   baseline, the first retrofit target, and a status for every adopted artifact.
   This file is write-blocked for agents — only the PI signs it (the brake).
3. A signed decision puts the project in **adoption mode**: the Model and
   Baseline-strategy gates become **satisfied-by-adoption**, so the first
   retrofit (e.g. a graduate-student reproducing the chosen figure) may run
   without a from-scratch model spec.
4. The **Baseline gate is NOT waived.** The chosen result must actually be
   reproduced and recorded in `docs/gates/baseline_registry.md` (route the first
   retrofit through baseline-strategy / baseline-validation) before any claim on
   it is validated. Adopted-but-unreproduced artifacts stay at `unknown`/`partial`
   and must not support strengthened claims.

## Output Format

### Existing State

Summarize what already exists.

### Validation Map

List artifacts and their current validation status.

### Main Risks

Name gaps that could affect scientific interpretation.

### First Retrofit Target

Recommend the smallest useful target.

### Researcher Decision

Ask what to validate, preserve, defer, or deprecate.
