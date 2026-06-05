---
name: researcher-review-loop
description: Use when presenting intermediate physics results, deciding next research steps, comparing iterations, asking a researcher to confirm interpretation, or recording scientific decisions.
---

# Researcher Review Loop Skill

Use this skill whenever a physics workflow produces an intermediate result that needs interpretation, prioritization, or approval from a human researcher.

## Goal

Keep the research process iterative, reviewable, and scientifically honest by separating output from interpretation and recording decisions.

## Review Packet

Prepare a compact packet with:

1. What changed in this iteration
2. Physical system, model, or dataset affected
3. Assumptions used
4. Parameters, units, and dimensions involved
5. Baseline and validation status
6. Figures, tables, or outputs produced
7. Claims currently supported
8. Claims not yet supported
9. Questions requiring researcher judgment
10. Recommended next action

## Researcher Questions

Ask questions that help choose the next scientific step:

- Does this result match physical intuition?
- Is the chosen toy model or reproduction target appropriate?
- Are the assumptions acceptable for the intended claim?
- Is the discrepancy physical, numerical, or likely an implementation issue?
- Should the next iteration refine the model, run validation, improve a figure, or revise the claim?

## Decision Logging

When `docs/process/researcher_review_log.md` exists, record each reviewable result.

When `docs/decision_log.md` exists, record decisions that affect:

- model scope
- assumptions
- parameter ranges
- validation requirements
- inclusion or exclusion of results
- manuscript interpretation

## Output Format

### Iteration Summary

State what changed and what was produced.

### Supported Interpretation

State only what the current evidence supports.

### Unsupported or Risky Interpretation

Name claims that should not yet be made.

### Researcher Check

List the specific questions for the researcher.

### Decision Needed

State the concrete decision required before the next iteration.

## When NOT to use this skill

- Routine progress pings or status updates that need no researcher interpretation, prioritization, or decision.
- Vetting a plan or campaign *before* any result exists -> use `research-plan-review`.
- Mapping or verifying a specific claim's evidence -> use `claim-to-evidence` or `scientific-verification-before-claim`.
- Establishing whether the result itself is numerically reliable -> use `numerical-validation`.
- A PI-owned decision gate is reached (`docs/gates/{orient,interview,model,seed}_decision.md`); record the proposal in the matching note/spec, but only the PI fills `## Decision` -- do not substitute this loop for the brake.
