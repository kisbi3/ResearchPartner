---
name: anomaly-debugging
description: Use when a physics result, simulation, plot, fit, derivation, unit check, conservation law, or reproduction behaves unexpectedly or contradicts assumptions.
---

# Anomaly Debugging Skill

Use this skill when a result is surprising, unstable, inconsistent, or physically suspicious.

## Core Rule

Do not patch the symptom. Classify and localize the anomaly first.

## Anomaly Classes

Classify the issue as one or more of:

- physical effect
- model misspecification
- invalid approximation
- dimensional or unit error
- boundary or initial condition issue
- numerical instability
- convergence failure
- solver or implementation bug
- data preprocessing error
- plotting or postprocessing error
- stochastic fluctuation
- interpretation overreach
- unknown

## Required Investigation

1. State the expected behavior and why it was expected.
2. State the observed behavior and how it was measured.
3. Reproduce the anomaly with the smallest command, derivation, or data slice.
4. Check recent changes in assumptions, parameters, seeds, boundary conditions, solver settings, and plotting code.
5. Isolate one variable at a time.
6. Test a simpler limit, toy model, or known benchmark.
7. Decide whether the anomaly is physical, numerical, implementation-related, data-related, or unresolved.
8. Record unresolved or important anomalies in `docs/logs/anomaly_log.md` when it exists.

## Minimal Tests

Prefer the smallest diagnostic:

- reduce the time step
- reduce or increase grid resolution
- set coupling to zero
- test a conservation law
- run deterministic seed
- compare raw output to plotted output
- check units for one equation
- run one analytically solvable limit

## Output Format

### Expected Behavior

State the prediction, assumption, or benchmark.

### Observed Behavior

State the discrepancy.

### Classification

Choose anomaly classes.

### Evidence Collected

List commands, plots, equations, or logs inspected.

### Current Hypothesis

State the most likely cause and confidence.

### Next Diagnostic

Name the smallest next test.
