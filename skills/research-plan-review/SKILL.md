---
name: research-plan-review
description: Use before executing a physics research plan, large simulation campaign, analysis workflow, figure set, reproduction attempt, or manuscript claim strategy.
---

# Research Plan Review Skill

Use this skill before starting substantial physics work.

## Goal

Catch missing baselines, unsupported claims, unclear assumptions, and validation gaps before time is spent on full-scale work.

## Required Plan Checks

Check whether the plan states:

1. Research question
2. Physical system
3. Model and governing equations
4. Assumptions and approximation regime
5. Parameters and units
6. Baseline validation target
7. Toy model or reproduction target
8. Numerical validation strategy
9. Expected observables
10. Failure criteria
11. Figure or table outputs
12. Claim-to-evidence path
13. Researcher review checkpoint
14. Reusable artifact expected from the iteration

## Plan Risk Labels

Use:

- `ready`: plan has enough validation structure to begin
- `needs baseline`: no toy, known limit, or reproduction target
- `needs assumptions`: physical assumptions are unclear
- `needs units`: parameters or equations lack units
- `needs validation`: convergence, stability, uncertainty, or conservation checks are missing
- `overclaims`: planned claim is stronger than planned evidence
- `too broad`: first iteration is not small enough

## Output Format

### Plan Status

Ready / needs revision.

### Missing Pieces

List missing assumptions, baselines, validation, units, or evidence.

### Main Scientific Risk

State the risk most likely to invalidate interpretation.

### Minimal Revision

Recommend the smallest change that makes the plan executable.

### Review Checkpoint

State when the researcher should inspect the next result.
