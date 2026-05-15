---
name: seed-design
description: Use after a research plan is approved by research-plan-review to convert it into concrete graduate-agent tasks with files, commands, inputs, outputs, pass/fail criteria, and failure handling. This is the Seed phase — do not begin coding or simulation before this skill produces a complete task specification.
---

# Seed Design Skill

Use this skill after `research-plan-review` marks a plan as `ready`. It converts an approved research plan into concrete, bounded tasks that Coding Subagents can execute without further clarification.

## Goal

Produce the smallest set of concrete, unambiguous tasks that can validate or advance the approved research plan. Each task must carry enough detail that a Coding Subagent can start without asking clarifying questions.

## Prerequisites

Confirm all of the following before running this skill:

1. The Interview Gate passes: `python scripts/check_interview_recorded.py --run <run-dir>`. If not, complete the professor-interview skill first.
2. The Literature Gate passes: `python scripts/check_literature_reviewed.py --run <run-dir>`. If not, complete literature-review-planning or create `docs/literature_skip_waiver.md` with a reason.
3. The Model Gate passes: `python scripts/check_model_specified.py --run <run-dir>`. If not, complete model-specification or create `docs/model_skip_waiver.md` with a reason.
4. The baseline validation target is identified.
5. The observables and failure criteria are defined.
6. The claim-to-evidence path is stated.

If any gate is unresolved, return to the appropriate skill before proceeding. Waivers lower the claim ceiling: literature skip → at most `interpretation`; model skip → at most `observation`.

## Task Structure

Each seed task must specify:

1. **Title**: a short imperative description of the task.
2. **Role**: Graduate Test-Design Agent, Coding Subagent, or Professor Orchestrator.
3. **Input files**: exact paths to code, data, parameter files, or prior output files.
4. **Command**: the exact command to run, including arguments and flags.
5. **Expected output**: exact file names, log entries, figure paths, or printed values.
6. **Pass criterion**: the specific condition that means this task succeeded.
7. **Fail criterion**: the specific condition that means this task failed and must not proceed.
8. **On failure**: what to do when the fail criterion is met — stop and escalate, log and continue, or retry with a stated change.
9. **Evidence record**: the file or log entry that will document the result for the Cartographer.

## Sizing Rule

The first seed task must be the **smallest possible** executable step. Reject a task that:

- runs more than one logical check at once
- produces output that requires a new decision before the next step is clear
- assumes the baseline is already validated if it has not been

If the plan requires multiple tasks, list them in dependency order. Mark which tasks may run in parallel and which must be sequential.

## Waiver Visibility

If any seed task bypasses a baseline, unit check, stability check, or evidence gate by waiver, mark that task explicitly with a waiver block:

```
[WAIVED GATE: <gate name>]
Waiver reason: <reason>
Risk remaining: <what could go wrong>
Required follow-up: <what must be validated later>
Claim ceiling: <observation | interpretation | mechanism | generalization | unsupported>
```

Waivers must appear inline in the task list, not only in a separate log. Invoke `cartographer-update` to record the waiver as a persistent workflow node.

## Researcher Checkpoint Rule

State when the researcher must inspect results before the next task begins. At minimum, define a checkpoint after:

- the first baseline task completes
- any task that produces a figure or table that will be interpreted
- any task where a waiver was applied

## Output Format

### Seed Summary

One paragraph: what this seed iteration tests, why it is the right first step, and what decision it enables.

### Task List

For each task:

#### Task N: [Title]

- **Role**:
- **Inputs**:
- **Command**:
- **Expected output**:
- **Pass criterion**:
- **Fail criterion**:
- **On failure**:
- **Evidence record**:

### Dependency Map

A simple ordered list or diagram showing which tasks depend on others and which may run in parallel.

### Researcher Checkpoint

State what the researcher must inspect and after which task, before the next phase begins.

### Cartographer Update

List the gate statuses, evidence links, and waivers to pass to `cartographer-update` when this seed is accepted.
