# Research Workflow Overview

This document is the pre-run overview for the physics research harness.

Before starting a substantial research task, inspect:

- `docs/workflow_map.html` for the interactive map
- `docs/workflow_diagrams.md` for the research workflow diagram
- `docs/paper_logic_diagram.md` when the work may become a paper
- `docs/workflow_code_map.md` for the file ownership map

## Workflow Summary

| Step | Purpose | Primary Gate | Responsible Files |
|---|---|---|---|
| Intake | Decide new project vs existing retrofit | Do not rewrite old artifacts before inventory | `skills/existing-research-onboarding/SKILL.md`, `docs/existing_project_intake.md` |
| Plan | Define question, model scope, observables, failure criteria | Plan has assumptions, units, baseline, claim path | `skills/research-plan-review/SKILL.md`, `docs/research_plan.md` |
| Specify model | Make equations, variables, parameters, and assumptions explicit | No silent boundary, seed, unit, or approximation changes | `skills/model-specification/SKILL.md`, `docs/assumptions.md` |
| Check dimensions | Verify units and nondimensionalization | Stop on dimensional inconsistency | `skills/dimensional-analysis/SKILL.md`, `PHYSICS.md` |
| Baseline gate | Validate toy, known limit, reproduction, or conservation case | No full-scale interpretation without pass or waiver | `skills/baseline-validation/SKILL.md`, `docs/baseline_registry.md` |
| Execute iteration | Run the smallest meaningful result | Record commands, parameters, seeds, outputs | `skills/numerical-validation/SKILL.md`, `docs/validation_log.md` |
| Anomaly branch | Diagnose surprising behavior | Classify before patching | `skills/anomaly-debugging/SKILL.md`, `docs/anomaly_log.md` |
| Researcher review | Show reviewable result to the researcher | Separate observation, interpretation, speculation | `skills/researcher-review-loop/SKILL.md`, `docs/researcher_review_log.md` |
| Claim gate | Convert result into safe wording | No claim without fresh or recorded evidence | `skills/scientific-verification-before-claim/SKILL.md`, `skills/claim-to-evidence/SKILL.md` |
| Retrospective | Preserve lineage and reusable artifacts | Each iteration leaves a check, log, benchmark, or decision | `skills/research-retrospective/SKILL.md`, `docs/lineage/iteration_template.md` |

## Interactive Navigation

Open `docs/workflow_map.html` in a browser. Click any node to see:

- purpose of the step
- required checks
- responsible skill files
- responsible docs
- responsible scripts

The HTML is generated from `docs/workflow_map.json` by:

```bash
python scripts/generate_workflow_map.py
```

Validate the links with:

```bash
python scripts/validate_workflow_links.py
```
