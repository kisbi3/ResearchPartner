---
name: numerical-validation
description: Use when running, reviewing, modifying, or interpreting simulations, numerical solvers, generated outputs, convergence checks, stability checks, or computational validation.
---

# Numerical Validation Skill

Use this skill when running, reviewing, or modifying simulations and numerical solvers.

## Goal

Determine whether numerical results are reliable enough for scientific interpretation.

## Required Validation Checks

### Reproducibility

- Are parameters recorded?
- Is the random seed recorded?
- Are input data and output paths recorded?
- Can the result be regenerated?

### Convergence

Check at least one when applicable:

- time-step convergence
- grid-size convergence
- sample-size convergence
- solver tolerance convergence
- finite-size scaling
- finite-time scaling

### Stability

Check:

- numerical stability
- sensitivity to integration scheme
- sensitivity to initial conditions
- sensitivity to boundary conditions

### Physical Sanity

Check:

- conservation laws
- positivity constraints
- boundedness
- equilibrium behavior
- limiting cases
- known analytical benchmarks

## Meeting Trigger

If the Validation Status is `needs more validation` and the cause is unclear — especially if convergence, stability, or physical sanity checks give contradictory signals — recommend a meeting:

```
Recommend: meeting --scope quick --on "<which checks failed and what the conflicting signals are>"
```

When numerical results are internally inconsistent (e.g., passes convergence but fails conservation), the root cause is often in the model or implementation design rather than in the parameters. A second perspective before tuning tolerances or adding complexity prevents compounding a hidden error.

## Output Format

### Validation Status

Ready / needs more validation / unreliable

### Commands Run

List commands.

### Checks Passed

List successful checks.

### Checks Failed

List failed or missing checks.

### Interpretation Risk

State what cannot yet be claimed.

### Next Validation

Recommend the next most important check.

## When NOT to use this skill

- Pure unit, dimension, scaling-law, or nondimensionalization questions with no run to validate -> use `dimensional-analysis`.
- A result, plot, fit, or reproduction is behaving unexpectedly or contradicting assumptions and the task is to find the cause -> use `anomaly-debugging` (return here once a fix is proposed and needs re-validation).
- Mapping a finished result onto a written claim or manuscript sentence -> use `claim-to-evidence` or `scientific-verification-before-claim`.
- Reviewing a plan before any code is run, where there are no numerical outputs yet to check -> use `research-plan-review`.
- Routine code edits, refactors, or runs with no convergence/stability/physical-sanity question and no result being interpreted scientifically.
