---
name: claim-to-evidence
description: Use when reviewing abstracts, introductions, results, discussions, conclusions, captions, manuscript text, or any scientific claim that needs evidence mapping.
---

# Claim-to-Evidence Skill

Use this skill when reviewing manuscript text, abstracts, introductions, results, discussions, or conclusions.

## Goal

Ensure every scientific claim is supported by an appropriate form of evidence.

## Claim Types

1. Definition
2. Assumption
3. Analytical result
4. Numerical result
5. Empirical result
6. Comparative result
7. Scaling claim
8. Mechanistic interpretation
9. Universality claim
10. Novelty claim
11. Limitation

## Evidence Types

Acceptable support includes:

- derivation
- theorem
- equation
- simulation result
- numerical convergence test
- experimental data
- figure
- table
- benchmark comparison
- citation
- explicitly stated assumption

## Red Flags

Mark a claim as risky if it:

- claims universality from one parameter regime
- claims causality from correlation
- claims mechanism from visual pattern only
- ignores boundary or initial conditions
- ignores finite-size or finite-time effects
- omits uncertainty
- uses undefined variables
- uses ambiguous terms such as "significant", "robust", or "emergent" without support

## Output Format

| Claim | Type | Evidence | Status | Revision |
|---|---|---|---|---|

Status options:

- Supported
- Partially supported
- Unsupported
- Overclaimed
- Needs derivation
- Needs citation
- Needs numerical validation
- Needs uncertainty estimate
