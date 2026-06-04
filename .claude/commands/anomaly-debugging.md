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

## Meeting Trigger

Once an anomaly is classified and a hypothesis is formed, recommend a meeting before patching:

```
Recommend: meeting --scope quick --on "<anomaly class and current hypothesis>"
```

Anomaly interpretation is the highest-risk moment for tunnel vision — the classification that feels most obvious is often the one being unconsciously anchored to. A short exchange with the professor, before any code changes, frequently reveals an overlooked cause.

Escalate to `--scope review` if the anomaly class is `unknown` after two diagnostic rounds, or if it could affect the core claim.

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

## Lineage Front-Matter

When an anomaly is significant enough to log, create an `errors/<slug>.err` file (or add a `lineage:` block to an entry in `docs/logs/anomaly_log.md`) with a `limits` edge to whatever downstream result, model, or claim is at risk:

```yaml
---
lineage:
  node_type: anomaly
  lineage_kind: anomaly
  status: blocked                   # or resolved / superseded when fixed
  requires_researcher_review: true
  limits:
    - result_<slug>                 # result, model, or claim this anomaly threatens
    - claim_<slug>
---
```

The `limits` edge is essential — it shows on the lineage graph which downstream result or claim is at risk. An anomaly with no outbound `limits` edge is flagged by `scripts/check_lineage_coverage.py`.

## Finding Lifecycle

When an anomaly or bug could affect a claim at `mechanism` or
`generalization`, record the finding in the affected
`docs/claims/<claim_id>.md` file under `## Finding Lifecycle`. Start as
`candidate`, then move only after an independent check to one of the resolved
states such as `validated_blocker`, `validated_limitation`, `false_alarm`,
`needs_researcher_judgment`, `evidence_linked`, or `researcher_reviewed`.

Do not let a candidate anomaly support promotion. If the anomaly limits or
blocks a claim, make the limitation visible in the claim file and lineage graph
instead of silently weakening the interpretation in conversation only.

When the anomaly is **resolved**, update `status` to `resolved` (or `superseded`) in the same file and re-run `/sync-workflow`. Do not delete the file — the audit trail of what was wrong and how it was fixed is part of the research record.

Run `/sync-workflow` after creating or updating the anomaly file to update the live workflow map. See `skills/sync-workflow/SKILL.md` for the full front-matter spec.
