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
