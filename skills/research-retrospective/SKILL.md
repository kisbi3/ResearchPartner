---
name: research-retrospective
description: Use after a physics research iteration, validation run, reproduction attempt, anomaly investigation, figure audit, manuscript revision, or researcher review.
---

# Research Retrospective Skill

Use this skill after an iteration to preserve what was learned and make the next iteration easier.

## Stage Completion Meeting

When a full research stage (Stage 0 literature review, Stage 1 algorithm validation, Stage 2 experiments, etc.) completes, convene a researcher meeting before starting the next stage. The meeting agenda must cover:

1. **Completion table**: list every task, its pass/fail status, and the evidence file.
2. **Numerical results summary**: key numeric outputs from validation (e.g. χ² p-values, relative errors).
3. **Harness evaluation**: did the agent pipeline work as designed? Identify failures (usage limits, wrong models, skipped logs).
4. **Design changes**: list any harness, template, or workflow rule changes triggered by this stage.
5. **Stage gate decision**: explicitly confirm or deny the gate for the next stage.

Record the meeting in `docs/process/research_retrospective.md` under a dated `## Stage N Meeting` heading. This is a blocking step — do not begin the next stage until the meeting record exists.

## Core Rule

Every research iteration should leave behind a reusable artifact, check, benchmark, log entry, template, or decision record.

## Retrospective Questions

Ask:

1. What changed?
2. What did we learn?
3. Which hypothesis, prediction, or assumption was tested?
4. What passed validation?
5. What failed or remained anomalous?
6. What claim became stronger, weaker, or unchanged?
7. What reusable artifact was created?
8. What should become a future check, warning, template, or skill rule?
9. What should be recorded in the lineage log?
10. What is the next smallest useful iteration?

## Compound Research Artifacts

Prefer producing one of:

- benchmark script
- toy model
- reproduction recipe
- dimensional check
- validation command
- figure audit entry
- hypothesis record
- anomaly record
- claim-to-evidence map
- decision log entry
- tacit pattern entry

## Output Format

### Iteration Outcome

Summarize what changed and what was learned.

### Evidence Delta

State which evidence became stronger, weaker, or unchanged.

### Reusable Artifact

Name what this iteration leaves behind.

### Lineage Entry

Record hypothesis, prediction, result, reflection, and next action.

### Next Iteration

Recommend the smallest next step.
