# Research Workflow Overview

This document is the pre-run overview for the physics research harness.

Research Partner is not a full automation system. It is a strong research partner that keeps assumptions, evidence, gates, and decisions visible so the researcher can understand and steer the work.

Before starting or continuing a substantial research task, inspect:

- `docs/workflow_map.html` for the live research workflow
- `docs/workflow_diagrams.md` for the research workflow diagram
- `docs/workflow_code_map.md` for the file ownership map

Generate `docs/workflow_map.html` as a live research workflow by default:

```bash
python scripts/generate_workflow_map.py
```

When the researcher explicitly starts manuscript planning, generate the paper logic workflow for review:

```bash
python scripts/generate_workflow_map.py --include-paper-logic
```

Do not show the paper logic workflow as a default research dashboard before the researcher asks to plan manuscript structure.

For substantial research iterations, keep a live Mermaid or workflow artifact current through a separate workflow-diagram agent or equivalent separate tracking pass. This live artifact should show the active step, gates, evidence links, blocked behaviors, and next researcher review checkpoint. It is a process-tracking artifact only and must not strengthen scientific claims beyond the evidence chain.

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

## Live Workflow Tracking

The workflow-diagram agent should update the live Mermaid/workflow artifact whenever the active step changes, a gate passes or blocks progress, an evidence link is added, a prohibited behavior is avoided, or the next review checkpoint changes. The live artifact should link to scripts, logs, figures, derivations, or decisions when they exist, and should mark missing evidence as missing rather than filling gaps with stronger wording.

## Professor-Led Orchestration

Substantial research plans, existing-project reviews, reproduction attempts, simulation campaigns, analysis pipelines, figure sets, and manuscript-claim work should be organized as a professor-led research group.

- The Professor Orchestrator owns scientific judgment, assumptions, model meaning, validation gates, evidence sufficiency, reproduction fidelity, and final claim discipline.
- Graduate Test-Design Agents interview the professor first, convert broad tasks into testable validation strategies, and then interview coding subagents to make implementation work concrete.
- Coding Subagents perform bounded implementation, analysis, or plotting tasks after the test strategy is clear. They report commands, parameters, seeds, outputs, validation status, and failures, but they should not decide that a result supports a stronger scientific claim.

The research group follows the evolutionary loop:

```text
Interview -> Seed -> Execute -> Evaluate
    ^                                 |
    +-------- Evolutionary Loop ------+
```

If evaluation exposes ambiguity, failed reproduction, dimensional risk, unsupported interpretation, or unclear workflow state, the loop returns to Interview.

## Diagram/Cartographer Agent

For substantial research iterations, the Diagram/Cartographer Agent maintains the live workflow artifact in real time. It listens to the Professor Orchestrator, Graduate Test-Design Agents, and Coding Subagents, then records active steps, interview checkpoints, seeds/specs, execution tasks, evaluation gates, evidence links, blocked behaviors, and the next researcher review checkpoint.

The Diagram/Cartographer Agent does not give project opinions, choose scientific interpretations, infer mechanisms, judge whether a claim is true, or strengthen claims. It is a process-tracking role only. Its artifact is a shared thinking surface for researcher review, not scientific evidence.

## Completion Conference

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Professor Orchestrator convenes a completion conference with all agents: graduate agents, coding subagents, and the Diagram/Cartographer Agent.

The completion conference should produce a user-facing report that summarizes:

- what each agent reports
- current workflow state
- visualization materials and evidence links
- supported claims
- unsupported or risky claims
- validation and reproduction status
- failures, caveats, and remaining uncertainty
- the next researcher decision or review checkpoint

## Interactive Navigation

Open `docs/workflow_map.html` in a browser. Click any node to see:

- purpose of the step
- required checks
- responsible skill files
- responsible docs
- responsible scripts

The default HTML is generated from the latest `ResearchPartner-runs/*/docs/live_workflow_diagram.md` artifact by:

```bash
python scripts/generate_workflow_map.py
```

The optional paper logic workflow is sourced from `docs/workflow_map.json` only when `--include-paper-logic` is passed.

Validate the links with:

```bash
python scripts/validate_workflow_links.py
```
