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

## Cartographer Update

Writing an entry to `docs/logs/anomaly_log.md` does not by itself add an anomaly node to the lineage graph (only `errors/*.err` does, via the workflow_hooks auto-emit). So when an anomaly is significant enough to log, also emit an explicit `anomaly` node:

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "anomaly_<short_slug>",
    "title": "<one-line description>",
    "node_type": "anomaly",
    "lineage_kind": "anomaly",
    "summary": "<expected vs observed in one sentence>",
    "status": "blocked",
    "requires_researcher_review": true,
    "graph_links": [
      {"from": "anomaly_<short_slug>", "to": "<node_id of the result, model, or claim it threatens>",
       "relation": "limits", "status": "fresh"}
    ]
  }
}'
```

The `limits` edge is essential — it shows on the lineage graph which downstream result, model, or claim is at risk until the anomaly is resolved. Do not omit it; an anomaly with no outbound edge looks unanchored and is easy to overlook in review (and is flagged by `scripts/check_lineage_coverage.py`).

### When the anomaly is resolved

Re-emit the same node with `status: "resolved"` (or `"superseded"`). `update_live_json.py` will automatically flip every outgoing `limits` edge on that node to `status: "superseded"`, so the lineage graph stops marking the downstream nodes as threatened:

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "anomaly_<same_slug>",
    "title": "<same title>",
    "node_type": "anomaly",
    "lineage_kind": "anomaly",
    "status": "resolved",
    "summary": "<one sentence on the fix and verifying check>"
  }
}'
```

Do not delete the anomaly node — the historical record of what was wrong and how it was fixed is part of the audit trail.
