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
4. The Baseline Strategy Gate passes: `python scripts/check_baseline_strategy.py --run <run-dir>`. If not, complete the baseline-strategy skill first. There is no skip waiver for this gate.
5. The observables and failure criteria are defined.
6. The claim-to-evidence path is stated.

If any gate is unresolved, return to the appropriate skill before proceeding. Waivers lower the claim ceiling: literature skip → at most `interpretation`; model skip → at most `observation`.

## Task 1 Rule

**Task 1 must always be the verification target defined in `docs/baseline_strategy.md`.**

- If `Decision = variation`: Task 1 reproduces the key result from the parent model, using the reproduce pass criterion stated in the strategy.
- If `Decision = new model`: Task 1 verifies code against Analytical Checkpoint 1, using the pass criterion stated in the strategy.

Do not design Task 1 as any other kind of work (e.g., parameter sweep, new feature, visualization). The baseline verification must come first. Execute Task 1 using the **`baseline-validation`** skill.

## Task Structure

Each seed task must specify:

1. **Title**: a short imperative description of the task.
2. **Role**: Graduate Student Agent (owns execution), Implementation Agent (code), Scientific Validator (run+check), or Professor Orchestrator.
3. **Input files**: exact paths to code, data, parameter files, or prior output files.
4. **Script to write**: exact path under `src/` for the Implementation Agent.
5. **Expected output**: exact file names, log entries, figure paths, or printed values.
6. **Pass criterion**: the specific condition that means this task succeeded.
7. **Fail criterion**: the specific condition that means this task failed and must not proceed.
8. **On failure**: what to do when the fail criterion is met — stop and escalate, log and continue, or retry with a stated change.
9. **Evidence record**: the file or log entry that will document the result for the Cartographer.
10. **Graduate Student Spawn Block**: the pre-formatted Agent() prompt the Professor uses to spawn a Graduate Student for this task (see format below).

### Graduate Student Spawn Block Format

Each task must end with a spawn block that Professor can use directly as the `prompt` argument to `Agent()`:

```
#### Graduate Student Spawn Block — Task N

You are a Graduate Student agent in a physics research group.
Load skills/graduate-student/SKILL.md to understand your role and constraints.

Run directory: <absolute path to run directory>

Task: <task title>
<2-3 sentence description of what to accomplish>

Implementation spec:
- Script to write: src/<filename>.py
- Equations: <exact equations with source>
- Parameters: <exact values with units>
- Algorithm: <method, timestep, convergence criterion>
- Outputs: <file paths the script must produce>

Pass criterion: <exact measurable criterion>
Fail criterion: <exact measurable criterion>
On failure: <escalate to Professor / log-and-continue / retry with [stated change]>
Evidence record: docs/gates/validation_log.md (append) + <any additional file>

Spawn sub-agents:
1. Implementation Agent (skills/implementation-agent/SKILL.md) to write the script.
2. Scientific Validator (skills/scientific-validator/SKILL.md) to run and check results.
3. Cache-Log Auditor (skills/cache-log-auditor/SKILL.md) to verify logs/ errors/ cache/ after Validator completes.

Report back: one-paragraph summary, scientific pass/fail verdict, cache-log audit verdict, observed values, evidence file path, anomalies if any.
```

## Sizing Rule

The first seed task must be the **smallest possible** executable step. Reject a task that:

- runs more than one logical check at once
- produces output that requires a new decision before the next step is clear
- assumes the baseline is already validated if it has not been

If the plan requires multiple tasks, list them in dependency order. Mark which tasks may run in parallel and which must be sequential.

## Task-Student Mapping Rule

**Each task in this seed corresponds to exactly one Graduate Student instance.** A Graduate Student is never reused across tasks, and a task is never split across multiple Graduate Students. Do not categorize tasks by "student type" (e.g. "baseline student tasks", "literature student tasks") — every Graduate Student has identical capabilities and is bound only to the single task they were spawned with.

When Professor Orchestrator reads this seed and spawns Graduate Students, the spawning protocol is:

- For every task with `depends_on: []` (no inbound dependency), Professor must spawn its Graduate Student in the **same assistant message** as every other independent task, using parallel `Agent()` tool calls in that one message.
- A task with `depends_on: [Task K]` is spawned only after Task K's Graduate Student reports back.

If your seed yields three independent tasks plus one dependent task, the expected spawning pattern is: one parallel batch of 3 Graduate Students, wait for those to return, then one more Graduate Student for the dependent task.

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

- **Role**: Graduate Student Agent
- **Inputs**:
- **Script to write**: `src/<filename>.py`
- **Expected output**:
- **Pass criterion**:
- **Fail criterion**:
- **On failure**:
- **Evidence record**:

#### Graduate Student Spawn Block — Task N

```
You are a Graduate Student agent in a physics research group.
Load skills/graduate-student/SKILL.md to understand your role and constraints.

Run directory: <absolute path>

Task: [Title]
[2-3 sentence description]

Implementation spec:
- Script to write: src/<filename>.py
- Equations: <equations>
- Parameters: <values with units>
- Algorithm: <method>
- Outputs: <file paths>

Pass criterion: <exact criterion>
Fail criterion: <exact criterion>
On failure: <action>
Evidence record: docs/gates/validation_log.md

Spawn sub-agents:
1. Implementation Agent (skills/implementation-agent/SKILL.md) to write the script.
2. Scientific Validator (skills/scientific-validator/SKILL.md) to run and check.
3. Cache-Log Auditor (skills/cache-log-auditor/SKILL.md) to verify logs/ errors/ cache/.

Report back: one-paragraph summary, scientific pass/fail verdict, cache-log audit verdict, observed values, evidence file path.
```

### Dependency Map

A simple ordered list or diagram showing which tasks depend on others and which may run in parallel. Use this exact format so the Professor Orchestrator can read it mechanically:

```
Task 1  depends_on: []           parallel_batch: A
Task 2  depends_on: []           parallel_batch: A
Task 3  depends_on: []           parallel_batch: A
Task 4  depends_on: [Task 1]     parallel_batch: B
Task 5  depends_on: [Task 1, Task 2]   parallel_batch: B
```

**Spawning rule:** all tasks in `parallel_batch: A` MUST be spawned by Professor in a single assistant message with multiple parallel `Agent()` calls. `parallel_batch: B` is spawned only after batch A's Graduate Students all report back. Sequential single-task spawning across messages, when no dependency forces it, is a workflow violation.

### Researcher Checkpoint

State what the researcher must inspect and after which task, before the next phase begins.

### Cartographer Update

List the gate statuses, evidence links, and waivers to pass to `cartographer-update` when this seed is accepted.
