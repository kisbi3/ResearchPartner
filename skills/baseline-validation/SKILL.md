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

## Waiver → Claim Ceiling Demotion

When the researcher issues a waiver, the following steps are mandatory before proceeding:

1. Add a `lineage:` front-matter block to the waiver artifact and run `/sync-workflow` to record the waiver as a visible graph node with status `active`.
2. The claim ceiling for all downstream work must be immediately lowered to `observation` and must remain there until a real baseline passes.
3. The waiver node stays visible in the live workflow artifact until the Lead Agent explicitly closes it by approving a completed baseline.

Do not silently absorb a waiver into a log entry. The lowered claim ceiling must be visible in the workflow map before any Execute or Evaluate phase work begins.

## Meeting Trigger

If the result is `fail` or `partial`, recommend a meeting before proceeding:

```
Recommend: meeting --scope quick --on "<what failed and what the expected behavior was>"
```

A failed or partial baseline means the model, code, or variation/new-model classification may be wrong. This is exactly the moment when working alone risks anchoring to the wrong explanation. The meeting does not need to be long — even a quick exchange with the professor often surfaces the overlooked assumption.

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

## Lineage Front-Matter

Add a `lineage:` block to the file recording this baseline result. If a comparison plot was produced, include `thumbnail_path`:

```yaml
---
lineage:
  node_type: result
  lineage_kind: result
  evidence_strength: strong         # or moderate for partial reproduction
  reproduces: paper_<paper_id>      # or analytical_<limit_slug> for new-model runs
  thumbnail_path: outputs/figures/baseline_comparison.png   # if produced
---
```

For a **failed or partial** baseline, also add a `lineage:` block to an `errors/*.err` file or `docs/logs/anomaly_log.md` entry with `node_type: anomaly` and a `limits` edge to whatever downstream claim it would block.

Then run `/sync-workflow` to update the live workflow map. See `skills/sync-workflow/SKILL.md` for the full front-matter spec.
