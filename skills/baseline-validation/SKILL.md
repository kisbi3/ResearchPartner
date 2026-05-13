---
name: baseline-validation
description: Use when starting a new physics model, solver, simulation, analysis pipeline, figure workflow, or manuscript interpretation that needs a toy model, known limit, benchmark, or reproduction check.
---

# Baseline Validation Skill

Use this skill before full-scale physics work when a smaller trusted target can test the model, code, analysis, or interpretation.

## Goal

Prevent premature scientific interpretation by requiring at least one baseline before trusting a new workflow.

## Baseline Types

Choose the smallest relevant baseline:

1. Toy model with known behavior
2. Analytically solvable limit
3. Reproduction of a published result
4. Reproduction of a previous validated output
5. Conservation-law sanity case
6. Dimensional sanity case
7. Simplified parameter regime

## Required Checks

For the selected baseline:

1. State what is being validated.
2. State why this baseline is relevant.
3. Record assumptions, parameters, initial conditions, and boundary conditions.
4. Record the command, derivation, or data source.
5. Compare observed behavior against the expected result.
6. Mark the status as pass, fail, partial, or waived.
7. Record interpretation limits before moving to full-scale work.

## Gate Rule

Do not proceed to full-scale simulation, production figures, or manuscript-level interpretation until at least one baseline validation has passed, unless the researcher explicitly waives the requirement.

If waived, record:

- who waived it
- why it was waived
- what risk remains
- what validation should be done later

## Output Format

### Baseline Target

Name the toy model, analytical limit, benchmark, or reproduced result.

### Expected Behavior

State the known or expected result.

### Validation Performed

List commands, derivations, comparisons, and checks.

### Result

Pass / fail / partial / waived.

### Interpretation Limits

State what this baseline does and does not justify.

### Next Action

Recommend whether to proceed, revise, or run another baseline.
