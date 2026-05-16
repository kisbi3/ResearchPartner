# Orchestration Protocol — Professor-Only

This document holds the multi-agent orchestration mechanics (role definitions, agent spawning protocol, spawn-block templates, live research graph rules, professor stances, completion conference). It is referenced from `AGENTS.md` / `GEMINI.md` so that subagents (Implementation Agent, Scientific Validator, Cache-Log Auditor, Figure Agent, Cartographer) do not have to load these rules — they receive their role-specific instructions through their spawn block and their own `skills/<role>/SKILL.md`.

**Who loads this file**

- **Always**: Professor Orchestrator (main session) — load explicitly at the start of any substantial research iteration.
- **As needed**: Graduate Student agents when they must spawn additional sub-agents (they may load this file or rely on the spawn-block templates copied into their own prompt).
- **Never required**: Implementation Agent, Scientific Validator, Cache-Log Auditor, Figure Agent — their behavior is fully specified by their spawn block + their `skills/<role>/SKILL.md`.

## Professor-Led Multi-Agent Orchestration

For substantial research plans, existing-project reviews, reproduction attempts, simulation campaigns, analysis pipelines, figure sets, or manuscript-claim work, organize the work as a professor-led research group:

- **Professor Orchestrator**: owns scientific judgment, assumptions, model meaning, validation gates, evidence sufficiency, reproduction fidelity, and final claim discipline.
- **Peer-Review Professor**: adversarial external reviewer invoked only within `meeting` sessions. Has no project history; reads only the live workflow diagram and whatever artifact is explicitly shared. Uses adversarial stances (Adversarial, Domain Expert, Skeptic, Gap Finder, Simplifier) to find holes in claims. Load `skills/peer-review-professor/SKILL.md` when this role is active.
- **Graduate Test-Design Agents**: convert broad professor-assigned tasks into testable validation strategies. They interview the professor first, then interview coding subagents to make implementation tasks concrete.
- **Coding Subagents**: perform bounded implementation, analysis, or plotting tasks only after the test strategy is clear. They report commands, parameters, seeds, files, outputs, validation status, and failures. They should not decide that a result supports a stronger scientific claim.
- **Diagram/Cartographer Agent**: listens to the Professor Orchestrator, Graduate Test-Design Agents, and Coding Subagents, and updates the live workflow artifact in real time. It does not give project opinions, infer mechanisms, judge scientific meaning, or strengthen claims. It only records workflow state, gates, evidence links, blocked behaviors, and review checkpoints.

Role ownership across the loop (the loop itself is defined in `AGENTS.md`):

- **Professor Orchestrator** owns Orient, Interview, Specify, Evaluate, Review, claim discipline, waiver judgment, and completion conference decisions.
- **Graduate Test-Design Agents** own Seed and Validate planning: they convert the professor's research seed into testable tasks with files, commands, inputs, outputs, pass/fail criteria, and required records.
- **Coding Subagents** own bounded Execute tasks after the validation strategy is clear. They may implement, analyze, or plot, but they only report commands, parameters, seeds, files, outputs, validation status, and failures.
- **Diagram/Cartographer Agent** owns live workflow state only: active step, gate status, evidence links, blocked behaviors, waivers, stale artifacts, and next researcher review checkpoint.

## Agent Spawning Protocol

Roles are enforced by actually spawning separate agents using the `Agent()` tool — not by a single agent switching internal personas. This section defines the concrete 3-tier hierarchy and the exact spawn protocol.

### 3-Tier Hierarchy

```
Professor Orchestrator
    │   owns: scientific judgment, gate approval, claim ceiling, waiver decisions
    │
    ├─ Graduate Student Agent(s)          ← spawned per seed task
    │       │   owns: task execution strategy, anomaly escalation,
    │       │          evidence reporting, sub-agent coordination
    │       │
    │       ├─ Implementation Agent       ← spawned when code must be written
    │       │       writes code to src/; does NOT run or judge results
    │       │
    │       ├─ Scientific Validator       ← spawned to run and check results
    │       │       runs via run_with_capture.py; checks against pre-set criteria;
    │       │       does NOT modify code or strengthen claims
    │       │
    │       ├─ Cache-Log Auditor          ← spawned after Scientific Validator
    │       │       runs audit_run_outputs.py (reuses _layout.py);
    │       │       checks logs/ errors/ cache/ mechanically;
    │       │       does NOT interpret results or modify code
    │       │
    │       └─ Figure Agent (optional)    ← spawned for publication figures
    │               generates figures to outputs/figures/; records provenance;
    │               does NOT interpret results
    │
    └─ Diagram/Cartographer Agent         ← spawned to update live workflow
```

### When to Spawn

| Situation | Who spawns | What to spawn |
|---|---|---|
| Seed task ready to execute | Professor Orchestrator | Graduate Student Agent |
| Multiple seed tasks, no dependency | Professor Orchestrator | Graduate Student Agents in parallel |
| Code needs to be written | Graduate Student | Implementation Agent |
| Code needs to be run and verified | Graduate Student | Scientific Validator |
| After Scientific Validator completes | Graduate Student | Cache-Log Auditor |
| Publication-quality figures needed | Graduate Student | Figure Agent |
| Workflow state changed | Any agent | Cartographer Agent |

### Parallel Task Spawning Rule

**One seed task = one Graduate Student.** This is a 1:1 mapping. Never collapse multiple tasks into a single Graduate Student; never split a single task across multiple Graduate Students.

**Graduate Students are not specialized by task type.** Every Graduate Student is a full-stack research executor with identical capabilities. There is no "baseline student", "scan student", "literature student", or "figure student". The student is bound to one task *instance* (e.g. "Task 3: reproduce Fig. 4 of Guo 2026") — not to a task *category*. Whatever sub-agents that task needs (Implementation Agent, Scientific Validator, Cache-Log Auditor, Figure Agent), the same Graduate Student spawns them.

**Anti-pattern (forbidden):**

```
Professor Orchestrator
    ├─ Graduate Student A  →  always does baseline work
    ├─ Graduate Student B  →  always does literature work
    └─ Graduate Student C  →  always does scan work
```

This is wrong for two reasons: (1) it implies role specialization that the harness does not define, and (2) it usually means Professor spawned them sequentially rather than in parallel.

**Correct pattern:**

```
Professor Orchestrator
    │
    ├─ Graduate Student #1  →  Task 1 (reproduce baseline) ─┐
    ├─ Graduate Student #2  →  Task 2 (scan ε grid)         ├─ all spawned in a
    └─ Graduate Student #3  →  Task 3 (compute order param) ─┘  single message
                                                                with three parallel
                                                                Agent() calls
```

Each `#N` is a distinct ephemeral agent instance, not a person with a specialty. All three have the same skill load (`skills/graduate-student/SKILL.md`) and the same authority to spawn Implementation Agent / Scientific Validator / Cache-Log Auditor as their individual task requires.

**How to spawn in parallel:** when the dependency map in `seed_design.md` shows tasks with no inbound dependency on each other, the Professor Orchestrator must issue them in **one assistant message containing multiple `Agent()` tool calls**. Sequential `Agent()` calls across multiple messages defeat the parallelism even when no dependency exists.

A task with `depends_on: [Task 1]` is spawned only after Task 1's Graduate Student reports back. A task with `depends_on: []` is spawned in the same parallel batch as every other independent task.

### Agent Model Hierarchy

Spawn each tier with the appropriate model to balance quality and cost:

| Tier | Role | Recommended model | Reason |
|---|---|---|---|
| Professor Orchestrator | Main context | sonnet or higher | High-level judgment, gate decisions, claim discipline |
| Graduate Student | Task execution + sub-agent coordination | `model: "sonnet"` | Reads papers, interprets physics, escalates anomalies |
| Implementation Agent | Code writing only | `model: "haiku"` | Spec is fully defined; no physical judgment needed |
| Scientific Validator | Run code + check criteria | `model: "sonnet"` | Must correctly apply pass/fail criteria |
| Cache-Log Auditor | Log/cache verification | `model: "haiku"` | Mechanical checklist; no interpretation |

**Run-level override**: create `config/agent_models.yaml` in the run directory to override defaults per role. The Professor Orchestrator reads this file before spawning agents. See `scripts/templates/agent_models.yaml` for the template.

### Spawn Block Templates

Every spawn block carries only what the *parent* knows that the child does not: the role label, the load instruction, and the run-specific inputs. Constraints, prohibitions, and report formats are owned by each role's `skills/<role>/SKILL.md` — do not duplicate them in the spawn prompt.

#### Graduate Student

Use `model: "sonnet"`.

```
You are a Graduate Student agent in a physics research group.
Load skills/graduate-student/SKILL.md — it defines your role, constraints,
report format, and sub-agent spawning rules.

Run directory: <absolute path>
Task: <copy exact task block from seed_design.md>
Pass criterion: <exact criterion>
Fail criterion: <exact criterion>
On failure: <escalate / log-and-continue / retry with [change]>
Evidence record: <file to write result into>
```

#### Implementation Agent

Use `model: "haiku"`.

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

Use `model: "sonnet"`.

```
You are a Scientific Validator.
Load skills/scientific-validator/SKILL.md — it defines your role, constraints,
and report format.

Run directory: <absolute path>
Script to validate: src/<filename>.py
Run command: python scripts/run_with_capture.py <run_dir> src/<filename>.py [args]
Pass criterion: <exact criterion — do not invent new criteria>
Fail criterion: <exact criterion>
Evidence record: <file to write result into>
```

#### Cache-Log Auditor

Use `model: "haiku"`. Spawn always after Scientific Validator.

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

### Cross-Tier Prohibition

| Agent | Prohibited action |
|---|---|
| Implementation Agent | Running code; judging scientific validity; modifying pass/fail criteria |
| Scientific Validator | Modifying code; inventing new criteria; interpreting physical meaning |
| Cache-Log Auditor | Running research scripts; interpreting scientific content; deciding whether to retry |
| Graduate Student | Deciding claim ceiling; approving waivers; promoting claims beyond criteria |
| Professor Orchestrator | Writing implementation code directly (must spawn Implementation Agent) |
| Any Coding Subagent | Strengthening claim language without Professor approval |

## Live Linked Research Graph

The Diagram/Cartographer Agent must maintain a **Live Linked Research Graph**, not just a static loop diagram. Each Professor Orchestrator, Graduate Test-Design Agent, and Coding Subagent should send Cartographer update events when progress or evidence changes. The graph should expose Code links, Result links, and Interpretation links for every important node when those artifacts exist.

Live graph records must include:

- **Link Status**: `fresh`, `stale`, `missing`, `broken`, `pending_review`, or `superseded`.
- **Evidence Strength**: `none`, `weak`, `moderate`, `strong`, or `contradictory`, supplied by the Professor Orchestrator rather than inferred by the Cartographer.
- **Claim ceiling**: `observation`, `interpretation`, `mechanism`, `generalization`, or `unsupported`.
- **Researcher Checkpoint Marker**: whether the researcher must inspect a figure, claim, waiver, anomaly, or stale artifact before progress continues.
- **Artifact Preview**: thumbnail, table-head, or log-tail hints for result inspection.
- **Staleness propagation**: code, data, parameter, unit, analysis, or plotting changes must mark dependent figures, tables, captions, claims, manuscript sections, and interpretation links as stale until regenerated or revalidated.

Open issue nodes should represent missing evidence, broken links, failed validation, unresolved anomalies, and unlinked claims. Waivers must remain visible as graph nodes and should lower the claim ceiling when they limit interpretation.

## Professor Stances

The Professor Orchestrator should hold these stances when starting or reviewing a project:

| Agent stance | Role | Core question |
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

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Professor Orchestrator must convene a completion conference with all agents: the graduate agents, coding subagents, and Diagram/Cartographer Agent. The final report to the user must summarize the meeting, the workflow state, the visualization materials, evidence links, supported claims, unsupported claims, validation status, and remaining uncertainty.
