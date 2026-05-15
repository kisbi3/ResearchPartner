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

Start a new run-specific artifact set from the harness templates with:

```bash
python scripts/start_research_run.py --name 1d-diffusion-mode-decay
```

The run scaffolder creates a sibling `ResearchPartner-runs/YYYY-MM-DD-<slug>/` directory with `docs/live_workflow_diagram.md`, `research_run_packet.md`, initial run docs, and `outputs/`.

When the researcher explicitly starts manuscript planning, generate the paper logic workflow for review:

```bash
python scripts/generate_workflow_map.py --include-paper-logic
```

Do not show the paper logic workflow as a default research dashboard before the researcher asks to plan manuscript structure.

For substantial research iterations, keep a live Mermaid or workflow artifact current through a separate workflow-diagram agent or equivalent separate tracking pass. This live artifact should show the active step, gates, evidence links, blocked behaviors, and next researcher review checkpoint. It is a process-tracking artifact only and must not strengthen scientific claims beyond the evidence chain.

## Scientific Loop Summary

The live research loop is:

```text
Orient -> Interview -> Specify -> Seed -> Validate -> Execute -> Evaluate -> Review -> Retrospect
    ^                                                                                 |
    +----------------------------- Evolutionary Loop ---------------------------------+
```

This loop absorbs software-development discipline into scientific practice. Brainstorming is the Professor-led Interview/Specify phase; implementation planning is the Graduate-led Seed/Validate phase; coding is bounded Execute work; code review and claim review are part of Evaluate/Review; branch or iteration finishing is Retrospect and lineage capture.

## Workflow Summary

| Step | Purpose | Primary Gate | Responsible Files |
|---|---|---|---|
| Orient | Classify task and choose roles | Task Intake Hook identifies scope and first professor question | `skills/task-intake/SKILL.md`, `AGENTS.md`, `GEMINI.md`, `docs/workflow_overview.md` |
| Interview | Clarify intent, assumptions, alternatives, and risk | Ambiguity Hook blocks execution when the research object is unclear | `skills/research-plan-review/SKILL.md`, `docs/research_plan.md` |
| Specify | Define model, variables, units, regimes, observables, and failure criteria | Assumption/Units, Unit Conversion, and Approximation Regime Hooks are satisfied | `skills/model-specification/SKILL.md`, `skills/dimensional-analysis/SKILL.md`, `docs/assumptions.md` |
| Seed | Convert the idea into the smallest testable research iteration | Graduate Test-Design Hook produces tasks with files, commands, outputs, and pass/fail criteria | `skills/seed-design/SKILL.md`, `skills/research-plan-review/SKILL.md`, `docs/research_plan.md` |
| Validate | Establish baseline, stability, reproducibility, and waiver status | Baseline Gate, Numerical Stability, Code-before-Test, and Waiver Hooks are satisfied | `skills/baseline-validation/SKILL.md`, `skills/numerical-validation/SKILL.md`, `docs/baseline_registry.md` |
| Execute | Run bounded implementation, analysis, simulation, or plotting tasks | Parameter Change, Data Lineage, Randomness/Reproducibility, Figure Provenance, and Environment Capture Hooks record provenance | `skills/numerical-validation/SKILL.md`, `docs/validation_log.md` |
| Evaluate | Separate observations, interpretation, speculation, and failures | Anomaly, Claim Strength, Literature Claim, Reviewer Simulation, and Negative Result Hooks check interpretation | `skills/anomaly-debugging/SKILL.md`, `skills/scientific-verification-before-claim/SKILL.md`, `skills/claim-to-evidence/SKILL.md` |
| Review | Present reviewable evidence and limits to the researcher | Manuscript Drift, Artifact Freshness, Scope Creep, and Cartographer Hooks expose stale or unsupported material | `skills/cartographer-update/SKILL.md`, `skills/researcher-review-loop/SKILL.md`, `docs/researcher_review_log.md` |
| Retrospect | Preserve lineage, decisions, failures, and reusable checks | Retrospective Hook leaves a reusable artifact, decision, open question, or skill/template rule | `skills/research-retrospective/SKILL.md`, `docs/research_retrospective.md`, `docs/lineage/iteration_template.md` |

## Hook Families

The hooks are grouped by the risk they control:

- Intake and scope: Task Intake Hook, Ambiguity Hook, Scope Creep Hook.
- Physical specification: Assumption/Units Hook, Unit Conversion Hook, Approximation Regime Hook.
- Validation and execution: Baseline Gate Hook, Graduate Test-Design Hook, Code-before-Test Hook, Numerical Stability Hook, Waiver Hook.
- Provenance and reproducibility: Parameter Change Hook, Randomness/Reproducibility Hook, Data Lineage Hook, Figure Provenance Hook, Environment Capture Hook.
- Evidence and claims: Claim Strength Hook, Literature Claim Hook, Manuscript Drift Hook, Artifact Freshness Hook, Reviewer Simulation Hook.
- Failure and memory: Anomaly Hook, Negative Result Hook, Cartographer Hook, Retrospective Hook.

## Live Linked Research Graph

The visible workflow map should not merely redraw the fixed loop. It should grow from the order in which research actually happens. Each Professor Orchestrator, Graduate Test-Design Agent, and Coding Subagent update should send a small Cartographer update event using `docs/run_templates/cartographer_update_template.md`. The Diagram/Cartographer Agent records those events as graph nodes and links, but does not judge scientific meaning.

Each important node should expose three link families:

- Code links: exact files and line numbers that define parameters, implement models, run validation, compute observables, or generate figures.
- Result links: figures, tables, logs, raw data, processed data, fit summaries, and other artifacts that the researcher can inspect immediately.
- Interpretation links: validation notes, decision records, researcher review notes, claim-to-evidence entries, waivers, caveats, and manuscript interpretation.

The graph tracks link state, not just link existence:

- Link Status: `fresh`, `stale`, `missing`, `broken`, `pending_review`, `superseded`.
- Evidence Strength: `none`, `weak`, `moderate`, `strong`, `contradictory`.
- Claim ceiling: `observation`, `interpretation`, `mechanism`, `generalization`, `unsupported`.
- Researcher Checkpoint Marker: whether the researcher must inspect the node before progress continues.
- Artifact Preview: thumbnail, table head, or log-tail hints for immediate inspection.

The graph should preserve both views:

- Chronological view: the order in which questions, decisions, runs, figures, anomalies, waivers, and reviews happened.
- Evidence view: how claims depend on code, parameters, baselines, runs, artifacts, interpretation notes, and reviewer checkpoints.

Staleness propagation is mandatory. When code, data, parameters, unit conversions, analysis, or plotting change, dependent figures, tables, captions, claims, manuscript sections, and interpretation links must become `stale` until regenerated or revalidated. Open issue nodes should represent missing evidence, broken links, failed validation, unresolved anomalies, and unlinked claims rather than hiding them.

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

Use `docs/run_templates/live_workflow_diagram_template.md` when starting a new run-specific live workflow artifact.

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

Use `docs/run_templates/research_run_packet_template.md` to keep Interview, Seed, Execute, Evaluate, Completion Conference, User Report, and Retrospective notes together without duplicating separate interview and report templates.

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
