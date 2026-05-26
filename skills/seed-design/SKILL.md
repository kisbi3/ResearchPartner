---
name: seed-design
description: Use after a research plan is approved by research-plan-review to convert it into concrete Lead-coordinated seed tasks with files, commands, inputs, outputs, pass/fail criteria, and failure handling. This is the Seed phase — do not begin coding or simulation before this skill produces a complete task specification.
---

# Seed Design Skill

Use this skill after `research-plan-review` marks a plan as `ready`. It converts an approved research plan into concrete, bounded tasks that Coding Subagents can execute without further clarification.

## Goal

Produce the smallest set of concrete, unambiguous tasks that can validate or advance the approved research plan. Each task must carry enough detail that a Coding Subagent can start without asking clarifying questions.

## Prerequisites

Confirm all of the following before running this skill:

1. The Interview Gate passes: `python scripts/check_interview_recorded.py --project <project-dir>`. If not, complete the professor-interview skill first.
2. The Literature Gate passes: `python scripts/check_literature_reviewed.py --project <project-dir>`. If not, complete literature-review-planning or create `docs/literature/literature_skip_waiver.md` with a reason.
3. The Model Gate passes: `python scripts/check_model_specified.py --project <project-dir>`. If not, complete model-specification or create `docs/plan/model_skip_waiver.md` with a reason.
4. The Baseline Strategy Gate passes: `python scripts/check_baseline_strategy.py --project <project-dir>`. If not, complete the baseline-strategy skill first. There is no skip waiver for this gate.
5. The observables and failure criteria are defined.
6. The claim-to-evidence path is stated.

If any gate is unresolved, return to the appropriate skill before proceeding. Waivers lower the claim ceiling: literature skip → at most `interpretation`; model skip → at most `observation`.

## Task 1 Rule

**Task 1 must always be the verification target defined in `docs/plan/baseline_strategy.md`.**

- If `Decision = variation`: Task 1 reproduces the key result from the parent model, using the reproduce pass criterion stated in the strategy.
- If `Decision = new model`: Task 1 verifies code against Analytical Checkpoint 1, using the pass criterion stated in the strategy.

Do not design Task 1 as any other kind of work (e.g., parameter sweep, new feature, visualization). The baseline verification must come first. Execute Task 1 using the **`baseline-validation`** skill.

## Task Structure

Each seed task must specify:

1. **Title**: a short imperative description of the task.
2. **Role**: Lead Agent acting in the Graduate Student role (owns orchestration), Implementation Agent (code), Scientific Validator (run+check), or Lead Agent.
3. **Input files**: exact paths to code, data, parameter files, or prior output files.
4. **Script to write**: exact path under `src/` for the Implementation Agent.
5. **Expected output**: exact file names, log entries, figure paths, or printed values.
6. **Pass criterion**: the specific condition that means this task succeeded.
7. **Fail criterion**: the specific condition that means this task failed and must not proceed.
8. **On failure**: what to do when the fail criterion is met — stop and escalate, log and continue, or retry with a stated change.
9. **Evidence record**: the file or log entry that `/sync-workflow` will use to refresh live workflow state.
10. **Lead Task-Orchestration Block**: the pre-formatted task packet the Lead Agent uses while loading `skills/graduate-student/SKILL.md` for this task (see format below).

### Lead Task-Orchestration Block Format

Each task ends with a Lead task-orchestration block. This is not an `Agent()` prompt and must not spawn a Graduate Student subagent. Use the canonical template in [`docs/orchestration_protocol.md`](../../docs/orchestration_protocol.md) under **Task-Orchestration Template → Graduate Student Role** — do not duplicate it here. Seed-design's job is to fill in the task-specific fields and append the **Implementation spec** block the Lead needs in order to spawn its leaf Implementation Agent:

```
Implementation spec:
- Script to write: src/<filename>.py
- Equations: <exact equations with source>
- Parameters: <exact values with units>
- Algorithm: <method, timestep, convergence criterion>
- Outputs: <file paths the script must produce>
```

Do not paste prohibitions ("Do NOT...") or the "Report back:" line into the block — those are owned by [`skills/graduate-student/SKILL.md`](../graduate-student/SKILL.md) and would only re-inject duplicate context into every task packet.

## Sizing Rule

The first seed task must be the **smallest possible** executable step. Reject a task that:

- runs more than one logical check at once
- produces output that requires a new decision before the next step is clear
- assumes the baseline is already validated if it has not been

If the plan requires multiple tasks, list them in dependency order. Mark which tasks may run in parallel and which must be sequential.

## Task-Orchestration Mapping Rule

**Each task in this seed corresponds to exactly one Lead-managed Graduate Student role pass.** Do not spawn Graduate Student subagents. Do not categorize tasks by "student type" (e.g. "baseline student tasks", "literature student tasks") — the Lead loads the same `graduate-student` role skill for each task and keeps orchestration in the main context.

When the Lead Agent reads this seed, the orchestration protocol is:

- For every task with `depends_on: []` (no inbound dependency), the Lead may coordinate the task packets as one batch, then directly spawn the needed leaf agents (`implementation-agent`, `scientific-validator`, `cache-log-auditor`) from the Lead context as task order permits.
- A task with `depends_on: [Task K]` begins only after Task K's Lead-managed role pass has produced its evidence and decision.

If your seed yields three independent tasks plus one dependent task, the expected pattern is: one Lead-managed batch of 3 task packets, wait for their required leaf-agent reports and Lead code reviews, then begin the dependent task.

## Waiver Visibility

If any seed task bypasses a baseline, unit check, stability check, or evidence gate by waiver, mark that task explicitly with a waiver block:

```
[WAIVED GATE: <gate name>]
Waiver reason: <reason>
Risk remaining: <what could go wrong>
Required follow-up: <what must be validated later>
Claim ceiling: <observation | interpretation | mechanism | generalization | unsupported>
```

Waivers must appear inline in the task list, not only in a separate log. Add a `lineage:` front-matter block to the waiver file and run `/sync-workflow` to record the waiver as a visible workflow node.

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

- **Role**: Lead Agent acting in the Graduate Student role
- **Inputs**:
- **Script to write**: `src/<filename>.py`
- **Expected output**:
- **Pass criterion**:
- **Fail criterion**:
- **On failure**:
- **Evidence record**:

#### Lead Task-Orchestration Block — Task N

Fill in the canonical Graduate Student Role template from [`docs/orchestration_protocol.md`](../../docs/orchestration_protocol.md) with this task's `Task:` description, `Pass criterion:`, `Fail criterion:`, `On failure:`, and `Evidence record:` values, then append the **Implementation spec** block (Script to write / Equations / Parameters / Algorithm / Outputs). Do not re-inject prohibitions or the report format — those belong to `skills/graduate-student/SKILL.md`.

### Dependency Map

A simple ordered list or diagram showing which tasks depend on others and which may run in parallel. Use this exact format so the Lead Agent can read it mechanically:

```
Task 1  depends_on: []           parallel_batch: A
Task 2  depends_on: []           parallel_batch: A
Task 3  depends_on: []           parallel_batch: A
Task 4  depends_on: [Task 1]     parallel_batch: B
Task 5  depends_on: [Task 1, Task 2]   parallel_batch: B
```

**Spawning rule:** the Lead Agent is the only spawner. Do not create Graduate Student subagents. For tasks in `parallel_batch: A`, the Lead may launch independent leaf agents in parallel only where their task dependencies permit; `parallel_batch: B` begins only after batch A's evidence and Lead decisions are recorded. Sequential single-task handling is acceptable when the Lead must preserve context or researcher review checkpoints.

### Researcher Checkpoint

State what the researcher must inspect and after which task, before the next phase begins.

### Lineage Front-Matter

After this seed is accepted, add a `lineage:` block to `docs/plan/baseline_strategy.md` (or any new decision file created for the seed) to record dependency and reproduction edges. Then run `/sync-workflow` to update the live workflow map. See `skills/sync-workflow/SKILL.md` for the front-matter spec.
