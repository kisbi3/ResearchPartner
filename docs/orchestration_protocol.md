# Orchestration Protocol — Single-Spawner Lead Agent + Leaf Agents

This document holds the multi-agent orchestration mechanics (role definitions, agent spawning protocol, spawn-block templates, live research graph rules, professor stances, completion conference). It is referenced from `AGENTS.md` / `GEMINI.md` so that subagents (Implementation Agent, Scientific Validator, Cache-Log Auditor, Peer-Review Professor) do not have to load these rules — they receive their role-specific instructions through their spawn block and their own `.claude/agents/<role>.md` definition plus `skills/<role>/SKILL.md`.

**Who loads this file**

- **Always**: Lead Agent (main session) — load explicitly at the start of any substantial research iteration.
- **As needed**: the Lead Agent when coordinating a seed task in the Graduate Student role.
- **Never required**: Implementation Agent, Scientific Validator, Cache-Log Auditor, Peer-Review Professor — their behavior is fully specified by their spawn block + their `.claude/agents/<role>.md` definition + their `skills/<role>/SKILL.md`.

## Roles

For substantial research plans, existing-project reviews, reproduction attempts, simulation campaigns, analysis pipelines, figure sets, or manuscript-claim work, organize the work as:

- **Lead Agent** (this is the main conversation context — *not* a spawned agent): owns scientific judgment, assumptions, model meaning, validation gates, evidence sufficiency, reproduction fidelity, and final claim discipline. The Lead Agent is also the *only* role that has direct two-way dialogue with the researcher; spawned agents are single-shot. The Lead Agent holds the "professor" stances (Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, Architect) as needed during Orient → Interview → Specify → Evaluate → Review.
- **Peer-Review Professor** (spawned subagent, `meeting --scope review` only): adversarial external reviewer with no project history; reads only the live workflow diagram and whatever artifact is explicitly shared. Uses adversarial stances (Adversarial, Domain Expert, Skeptic, Gap Finder, Simplifier) to find holes in claims. Load `skills/peer-review-professor/SKILL.md`. Single-shot critique, then done.
- **Graduate Student role** (not spawned): a Lead-Agent operating mode loaded from `skills/graduate-student/SKILL.md` for one seed task. It owns task execution strategy, Lead code review, anomaly escalation, and evidence reporting in the main context. The Lead directly spawns any leaf agents this role needs.
- **Leaf Coding Subagents** (spawned directly by the Lead Agent): Implementation Agent, Scientific Validator, and Cache-Log Auditor perform bounded implementation, validation, audit, analysis, or plotting tasks only after the Lead's task strategy is clear. They report commands, parameters, seeds, files, outputs, validation status, and failures. They never spawn other agents or decide that a result supports a stronger scientific claim.
- **Workflow state automation** (*not* a spawned agent): the live workflow artifact is maintained automatically by `scripts/workflow_hooks.py` (registered as PreToolUse/PostToolUse on the `Agent` tool) and by explicit `/sync-workflow` refreshes. There is no separate diagram agent to spawn. The contract is to record process state only; never strengthen claims, infer mechanisms, or judge meaning.

Role ownership across the loop (the loop itself is defined in `AGENTS.md`):

- **Lead Agent** owns Orient, Interview, Specify, Evaluate, Review, claim discipline, waiver judgment, and completion conference decisions.
- **Lead Agent in the Graduate Student role** owns Seed and Validate planning for one task: converting the research seed into testable files, commands, inputs, outputs, pass/fail criteria, and required records.
- **Leaf Coding Subagents** own bounded Execute tasks after the validation strategy is clear. They may implement, validate, audit, analyze, or plot, but they only report commands, parameters, seeds, files, outputs, validation status, and failures.
- **workflow_hooks.py (hook-driven, not spawned)** records spawn events automatically; `/sync-workflow` refreshes active step, gate status, evidence links, blocked behaviors, waivers, stale artifacts, and next researcher review checkpoint.

## Agent Spawning Protocol

The Lead Agent is the only spawner. Live testing showed spawned subagents do not receive the `Agent` tool, so nested spawning is not part of the harness contract. Graduate Student is therefore a Lead-loaded role, not a spawned tier. Leaf roles are enforced by actually spawning separate agents using the `Agent()` tool with explicit `subagent_type` values.

### Single-Spawner Hierarchy

```
Lead Agent (main context — not spawned)
    │   owns: dialogue with researcher, scientific judgment, gate approval,
    │          claim ceiling, waiver decisions, professor stances,
    │          Graduate Student role for seed-task orchestration
    │
    ├─ Peer-Review Professor              ← spawned only in meeting --scope review
    │       single-shot adversarial critique; reads shared artifacts; done
    │
    ├─ Implementation Agent               ← spawned by Lead when code must be written
    │       writes code to src/; does NOT run, spawn, or judge results
    │
    ├─ Scientific Validator               ← spawned by Lead to run and check results
    │       runs via run_with_capture.py; checks against pre-set criteria;
    │       does NOT modify code, spawn, or strengthen claims
    │
    ├─ Cache-Log Auditor                  ← spawned by Lead after Scientific Validator
    │       runs audit_run_outputs.py (reuses _layout.py);
    │       checks logs/ errors/ cache/ mechanically;
    │       does NOT interpret results, modify code, or spawn
    │
    ├─ Figure generation                  ← Implementation Agent work
    │       writes requested figure-generation code/files to outputs/figures/;
    │       does NOT interpret results
    │
    └─ workflow_hooks.py (hook-driven, not spawned)
            automatic Agent spawn records + /sync-workflow refreshes
```

### When to Spawn

| Situation | Who spawns | What to spawn |
|---|---|---|
| Seed task ready to execute | Lead Agent | No subagent; load `skills/graduate-student/SKILL.md` in the Lead context |
| Multiple seed tasks, no dependency | Lead Agent | Coordinate a Lead-managed task batch; spawn leaf agents directly where task dependencies permit |
| Adversarial review needed before promoting a claim | Lead Agent | Peer-Review Professor (via `meeting --scope review`) |
| Code needs to be written | Lead Agent | Implementation Agent |
| Code needs to be run and verified | Lead Agent | Scientific Validator |
| After Scientific Validator completes | Lead Agent | Cache-Log Auditor |
| Publication-quality figures needed | Lead Agent | Implementation Agent |
| Workflow state changed | Automatic + Lead-triggered | `workflow_hooks.py` records Agent spawns; `/sync-workflow` refreshes state |

### Parallel Task Coordination Rule

**One seed task = one Lead-managed Graduate Student role pass.** Do not spawn Graduate Student subagents. Never split a single seed task across multiple orchestration roles; the Lead owns the task packet and any leaf-agent reports.

**Graduate Student is not a subagent type.** It is the Lead's task-orchestration role. There is no "baseline student", "scan student", "literature student", or "figure student". The role pass is bound to one task *instance* (e.g. "Task 3: reproduce Fig. 4 of Guo 2026") — not to a task *category*. Whatever leaf agents that task needs (Implementation Agent, Scientific Validator, Cache-Log Auditor), the Lead spawns them directly.

**Anti-pattern (forbidden):**

```
Lead Agent
    ├─ Graduate Student subagent A  →  always does baseline work
    ├─ Graduate Student subagent B  →  always does literature work
    └─ Graduate Student subagent C  →  always does scan work
```

This is wrong for two reasons: (1) Graduate Student is not a spawned role, and (2) it implies role specialization that the harness does not define.

**Correct pattern:**

```
Lead Agent
    │
    ├─ Task 1 Graduate Student role pass → leaf agents as needed
    ├─ Task 2 Graduate Student role pass → leaf agents as needed
    └─ Task 3 Graduate Student role pass → leaf agents as needed
```

Each task pass uses the same `skills/graduate-student/SKILL.md` role instructions in the Lead context. The Lead may issue multiple independent leaf-agent `Agent()` calls in one assistant message when the dependency map permits.

**How to use parallelism:** when the dependency map in `seed_design.md` shows leaf implementation or validation jobs with no inbound dependency on each other, the Lead Agent may issue them in one assistant message containing multiple `Agent()` tool calls. Do not create Graduate Student subagents to get parallelism.

A task with `depends_on: [Task 1]` begins only after Task 1's evidence and Lead decision are recorded.

### Agent Model Hierarchy

Spawn each spawned tier with the appropriate model to balance quality and cost. The Lead Agent runs in whatever model the researcher chose for the main session; the table below applies only to spawned subagents.

| Tier | Role | Recommended model | Reason |
|---|---|---|---|
| Lead Agent | Main context | (session default) | Holds dialogue + judgment; not spawned |
| Graduate Student role | Lead-loaded task orchestration | (session default) | Keeps coordination and code review in the Lead context |
| Implementation Agent | Leaf code writing only | `model: "haiku"` | Spec is fully defined; no physical judgment needed |
| Scientific Validator | Leaf run code + check criteria | `model: "sonnet"` | Must correctly apply pass/fail criteria |
| Cache-Log Auditor | Leaf log/cache verification | `model: "haiku"` | Mechanical checklist; no interpretation |
| Peer-Review Professor | Leaf adversarial review | `model: "sonnet"` or higher | Must produce substantive critique |

**Run-level override**: create `config/agent_models.yaml` in the run directory to override defaults per role. The Lead Agent reads this file before spawning agents. See `scripts/templates/agent_models.yaml` for the template.

### Role Agent Definitions And Tools

Claude Code loads `.claude/agents/<role>.md` for the selected leaf `subagent_type` and applies that file's `tools:` frontmatter at runtime. The harness records the same leaf-role contract in `docs/harness/spawn_contracts.json`; `python scripts/check_spawn_contracts.py --project <project-dir>` is the offline consistency gate that verifies the agent file, skill declaration, tools list, empty child-spawn declarations, and description hygiene agree. It is not a substitute for runtime tool isolation.

Every role-agent description must start with `Explicitly spawned only` and must not contain auto-trigger examples such as "Use this agent when" or "Trigger when". This reduces opportunistic auto-delegation; it is a hygiene rule, not a hard runtime firewall.

The `Agent` tool is reserved for the Lead Agent. In plain checker terms: Agent tool is reserved for the Lead Agent. No `.claude/agents/<role>.md` leaf definition may list `Agent` in `tools:`, and no leaf role may declare child `subagent_type` values.

| Role | `subagent_type` | Agent tools | Static scope |
|---|---|---|---|
| Implementation Agent | `implementation-agent` | `Read, Write, Edit, Grep, Glob` | leaf agent; writes code/figure files from a precise spec; no code execution, claim judgment, or spawning |
| Scientific Validator | `scientific-validator` | `Read, Grep, Glob, Bash` | leaf agent; runs validation commands and reports exact values; no Write/Edit or spawning |
| Cache-Log Auditor | `cache-log-auditor` | `Read, Grep, Glob, Bash` | leaf agent; runs audit commands and reports artifact sufficiency; no Write/Edit or spawning |
| Peer-Review Professor | `peer-review-professor` | `Read, Grep, Glob` | leaf agent; reads shared artifacts only; invoked only inside `meeting --scope review/full` |

### Task-Orchestration Template

The Graduate Student role template is a Lead-context task packet, not an `Agent()` spawn block.

#### Graduate Student Role

```text
Lead Agent: load skills/graduate-student/SKILL.md for this one seed task.
Run directory: <absolute path>
Task: <copy exact task block from seed_design.md>
Pass criterion: <exact criterion>
Fail criterion: <exact criterion>
On failure: <escalate / log-and-continue / retry with [change]>
Evidence record: <file to write result into>
```

### Leaf Spawn Block Templates

Every leaf spawn block carries only what the Lead knows that the child does not: the role label, the load instruction, and the run-specific inputs. Constraints, prohibitions, and report formats are owned by each role's `.claude/agents/<role>.md` and `skills/<role>/SKILL.md` — do not duplicate them in the spawn prompt.

#### Implementation Agent

Use `model: "haiku"` and `subagent_type: implementation-agent`.

```
You are an Implementation Agent.
Load skills/implementation-agent/SKILL.md — it defines your role, constraints,
and report format.

Run directory: <absolute path>
Write to: src/<filename>.py
Specification:
  - Equations: <exact equations>
  - Parameters: <exact parameters with units>
  - Algorithm: <method, step size, stopping criterion>
  - Inputs: <what the script should accept>
  - Outputs: <what the script should produce and where>
```

#### Scientific Validator

Use `model: "sonnet"` and `subagent_type: scientific-validator`.

```
You are a Scientific Validator.
Load skills/scientific-validator/SKILL.md — it defines your role, constraints,
and report format.

Run directory: <absolute path>
Script to validate: src/<filename>.py
Run command: python scripts/run_with_capture.py --quiet <run_dir> src/<filename>.py [args]
Pass criterion: <exact criterion — do not invent new criteria>
Fail criterion: <exact criterion>
Evidence record: <file to write result into>
```

#### Cache-Log Auditor

Use `model: "haiku"` and `subagent_type: cache-log-auditor`. Spawn always after Scientific Validator.

```
You are a Cache-Log Auditor.
Load skills/cache-log-auditor/SKILL.md — it defines your role, constraints,
and report format.

Run directory: <absolute path>
Script stem: <filename without .py>
Log path: <log file path from Scientific Validator's report>
Expected cache files (relative to run_dir):
  - <cache/filename1.npy>   ← omit section if no cache files are required
Min numeric lines: <N>      ← default 3 if not specified in task

Run: python scripts/audit_run_outputs.py <run_dir> <stem> --log <log_path> \
     [--expect-cache <rel_path> ...] [--min-numeric <N>]
Evidence record: docs/gates/validation_log.md
```

#### Peer-Review Professor

Use `model: "sonnet"` or higher and `subagent_type: peer-review-professor`. Spawn only from `meeting --scope review` or `meeting --scope full`.

```
You are a Peer-Review Professor.
Load skills/peer-review-professor/SKILL.md — it defines your adversarial
review role, evidence limits, and verdict format.

Meeting scope: review
Shared artifacts:
  - <live workflow diagram path>
  - <claim/evidence/figure/manuscript excerpt path>
Question under review: <specific claim or decision>
```

### Cross-Tier Prohibition

| Agent | Prohibited action |
|---|---|
| Implementation Agent | Running code; judging scientific validity; modifying pass/fail criteria |
| Scientific Validator | Modifying code; inventing new criteria; interpreting physical meaning |
| Cache-Log Auditor | Running research scripts; interpreting scientific content; deciding whether to retry |
| Lead Agent in Graduate Student role | **Writing or patching code** (must re-spawn Implementation Agent for every change); strengthening claims before evidence review |
| Lead Agent | Writing implementation code directly (must spawn Implementation Agent); skipping Lead code review before Validator handoff |
| Any leaf Coding Subagent | Spawning agents; strengthening claim language without Lead Agent approval |

## Live Linked Research Graph

The workflow automation must maintain a **Live Linked Research Graph**, not just a static loop diagram. The Lead Agent and leaf Coding Subagents leave evidence and lineage records when progress changes; `workflow_hooks.py` supplements these with automatic Agent activity records, and `/sync-workflow` rebuilds the visible state. The graph should expose Code links, Result links, and Interpretation links for every important node when those artifacts exist.

Live graph records must include:

- **Link Status**: `fresh`, `stale`, `missing`, `broken`, `pending_review`, or `superseded`.
- **Evidence Strength**: `none`, `weak`, `moderate`, `strong`, or `contradictory`, supplied by the Lead Agent rather than inferred by workflow automation.
- **Claim ceiling**: `observation`, `interpretation`, `mechanism`, `generalization`, or `unsupported`.
- **Researcher Checkpoint Marker**: whether the researcher must inspect a figure, claim, waiver, anomaly, or stale artifact before progress continues.
- **Artifact Preview**: thumbnail, table-head, or log-tail hints for result inspection.
- **Staleness propagation**: code, data, parameter, unit, analysis, or plotting changes must mark dependent figures, tables, captions, claims, manuscript sections, and interpretation links as stale until regenerated or revalidated.

Open issue nodes should represent missing evidence, broken links, failed validation, unresolved anomalies, and unlinked claims. Waivers must remain visible as graph nodes and should lower the claim ceiling when they limit interpretation.

## Lead Agent Stances

The Lead Agent holds these stances (the "professor stances") when starting or reviewing a project. They are mental modes the Lead Agent adopts during dialogue, not separate spawned agents:

| Stance | Role | Core question |
|---|---|---|
| Socratic Interviewer | Questions-only. Never builds. | What are you assuming? |
| Ontologist | Finds essence, not symptoms. | What is this, really? |
| Seed Architect | Crystallizes specs from dialogue. | Is this complete and unambiguous? |
| Evaluator | Performs staged verification. | Did we build the right thing? |
| Contrarian | Challenges every assumption. | What if the opposite were true? |
| Hacker | Finds unconventional paths. | What constraints are actually real? |
| Simplifier | Removes complexity. | What is the simplest thing that could work? |
| Researcher | Stops coding and starts investigating. | What evidence do we actually have? |
| Architect | Identifies structural causes. | If we started over, would we build it this way? |

## Completion Conference

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Lead Agent must convene a completion conference summarizing all leaf-agent reports, Graduate Student role output, and the latest workflow state. The final report to the user must summarize the meeting, the workflow state, the visualization materials, evidence links, supported claims, unsupported claims, validation status, and remaining uncertainty.
