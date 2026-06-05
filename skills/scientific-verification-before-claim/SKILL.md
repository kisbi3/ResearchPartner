---
name: scientific-verification-before-claim
description: Use before making, strengthening, publishing, summarizing, captioning, or manuscript-editing a physics claim that depends on equations, simulations, figures, data, or citations.
---

# Scientific Verification Before Claim Skill

Use this skill before turning a result into a scientific claim.

## Core Rule

No claim without fresh evidence.

Do not say a result "shows", "proves", "demonstrates", "reveals", "confirms", or "establishes" something unless the required evidence has been checked in the current task or is explicitly recorded.

## Claim Upgrade Ladder

Use the weakest language supported by evidence:

1. speculation
2. qualitative analogy
3. observed numerical pattern
4. validated numerical result
5. controlled approximation
6. exact analytical result
7. independently reproduced or empirically supported result

Do not present a lower rung as a higher rung.

## Required Checks

Before accepting or strengthening a claim, identify which checks are needed:

- assumptions recorded
- variables and units defined
- dimensional consistency checked
- baseline, toy model, known limit, or reproduction passed
- numerical convergence or stability checked
- conservation laws checked where applicable
- uncertainty or error estimate provided
- figure/table supports the stated interpretation
- citation or prior result exists for novelty or comparison claims
- researcher reviewed interpretation when judgment is needed

## Red Flags

Downgrade or block claims that:

- infer mechanism from visual agreement alone
- infer causality from correlation
- claim universality from one parameter regime
- omit finite-size, finite-time, discretization, or statistical uncertainty
- hide failed runs or anomalies
- use undefined variables or ambiguous units
- assert novelty without literature support
- use "robust", "significant", "emergent", or "generic" without a defined test

## Output Format

### Claim

Quote or summarize the claim.

### Evidence Status

Supported / partially supported / unsupported / overclaimed / speculative.

### Required Evidence

List the checks required for this claim level.

### Evidence Found

List the derivations, logs, scripts, figures, data, validation checks, or citations found.

### Safe Wording

Give the strongest wording justified by the evidence.

### Missing Work

Name the smallest validation or citation needed to strengthen the claim.

### Finding Lifecycle

If the claim ceiling is `mechanism` or `generalization`, verify that the claim
file at `docs/claims/<claim_id>.md` contains a `## Finding Lifecycle` section.
The lifecycle must no longer be `candidate`, must include
`independently_checked` and `evidence_linked`, must not be `false_alarm`, and
must list at least one existing project path under `## Evidence Paths Read
Directly`.

This check is structural. It confirms declared evidence paths exist; it does not
prove that the Lead Agent read them. The Lead remains responsible for direct
reading before strengthening the claim.

## When NOT to use this skill

- Routine writing, notes, or status updates that make or strengthen no scientific claim.
- Mapping many existing claims in a manuscript to evidence in one sweep -> use `claim-to-evidence`.
- Establishing whether a numerical result is reliable in the first place (convergence/stability/conservation) -> use `numerical-validation`.
- Pure unit or dimensional-consistency checks with no claim being made -> use `dimensional-analysis`.
- An unexpected or contradictory result needs its cause found before any claim is even considered -> use `anomaly-debugging`.
