# Orchestration Protocol — Lead Agent + Spawned Tiers

This document holds the multi-agent orchestration mechanics (role definitions, agent spawning protocol, spawn-block templates, live research graph rules, professor stances, completion conference). It is referenced from `AGENTS.md` / `GEMINI.md` so that subagents (Implementation Agent, Scientific Validator, Cache-Log Auditor, Peer-Review Professor) do not have to load these rules — they receive their role-specific instructions through their spawn block and their own `.claude/agents/<role>.md` definition plus `skills/<role>/SKILL.md`.

**Who loads this file**

- **Always**: Lead Agent (main session) — load explicitly at the start of any substantial research iteration.
- **As needed**: Graduate Student agents when they must spawn additional sub-agents (they may load this file or rely on the spawn-block templates copied into their own prompt).
- **Never required**: Implementation Agent, Scientific Validator, Cache-Log Auditor, Peer-Review Professor — their behavior is fully specified by their spawn block + their `.claude/agents/<role>.md` definition + their `skills/<role>/SKILL.md`.

## Roles

For substantial research plans, existing-project reviews, reproduction attempts, simulation campaigns, analysis pipelines, figure sets, or manuscript-claim work, organize the work as:

- **Lead Agent** (this is the main conversation context — *not* a spawned agent): owns scientific judgment, assumptions, model meaning, validation gates, evidence sufficiency, reproduction fidelity, and final claim discipline. The Lead Agent is also the *only* role that has direct two-way dialogue with the researcher; spawned agents are single-shot. The Lead Agent holds the "professor" stances (Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, Architect) as needed during Orient → Interview → Specify → Evaluate → Review.
- **Peer-Review Professor** (spawned subagent, `meeting --scope review` only): adversarial external reviewer with no project history; reads only the live workflow diagram and whatever artifact is explicitly shared. Uses adversarial stances (Adversarial, Domain Expert, Skeptic, Gap Finder, Simplifier) to find holes in claims. Load `skills/peer-review-professor/SKILL.md`. Single-shot critique, then done.
- **Graduate Test-Design Agents** (spawned): convert broad Lead-Agent-assigned tasks into testable validation strategies. They interview their parent (the Lead Agent) first via the spawn block, then spawn Coding Subagents as needed. Graduate Students **read and review code but do not write it** — if any code must change, they re-spawn the Implementation Agent with a precise correction list. Code review (equation fidelity, parameter values, seeds, output discipline) is a mandatory step between Implementation Agent and Scientific Validator.
- **Coding Subagents** (spawned by Graduate Students): perform bounded implementation, validation, audit, analysis, or plotting tasks only after the test strategy is clear. They report commands, parameters, seeds, files, outputs, validation status, and failures. They never decide that a result supports a stronger scientific claim.
- **Diagram/Cartographer** (*not* a spawned agent — hook-driven automation): the live workflow artifact is maintained automatically by `scripts/workflow_hooks.py` (registered as PreToolUse/PostToolUse on the `Agent` tool) and by explicit `cartographer-update` SKILL packets that any agent can emit. There is no separate Cartographer agent to spawn. The role exists as a contract (record process state only; never strengthen claims, infer mechanisms, or judge meaning), implemented by hooks + SKILL.

Role ownership across the loop (the loop itself is defined in `AGENTS.md`):

- **Lead Agent** owns Orient, Interview, Specify, Evaluate, Review, claim discipline, waiver judgment, and completion conference decisions.
- **Graduate Test-Design Agents** own Seed and Validate planning: they convert the Lead Agent's research seed into testable tasks with files, commands, inputs, outputs, pass/fail criteria, and required records.
- **Coding Subagents** own bounded Execute tasks after the validation strategy is clear. They may implement, validate, audit, analyze, or plot, but they only report commands, parameters, seeds, files, outputs, validation status, and failures.
- **Cartographer (automated)** records live workflow state only: active step, gate status, evidence links, blocked behaviors, waivers, stale artifacts, and next researcher review checkpoint.

## Agent Spawning Protocol

Roles below the Lead Agent are enforced by actually spawning separate agents using the `Agent()` tool — not by the Lead Agent silently doing the work itself. This section defines the concrete 2-tier hierarchy and the exact spawn protocol.

### 2-Tier Spawn Hierarchy

```
Lead Agent (main context — not spawned)
    │   owns: dialogue with researcher, scientific judgment, gate approval,
    │          claim ceiling, waiver decisions, professor stances
    │
    ├─ Peer-Review Professor              ← spawned only in meeting --scope review
    │       single-shot adversarial critique; reads shared artifacts; done
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
    │       └─ Figure generation          ← Implementation Agent work
    │               writes requested figure-generation code/files to
    │               outputs/figures/; does NOT interpret results
    │
    └─ Cartographer (hook-driven, not spawned)
            workflow_hooks.py + cartographer-update SKILL packets
```

### When to Spawn

| Situation | Who spawns | What to spawn |
|---|---|---|
| Seed task ready to execute | Lead Agent | Graduate Student Agent |
| Multiple seed tasks, no dependency | Lead Agent | Graduate Student Agents in parallel |
| Adversarial review needed before promoting a claim | Lead Agent | Peer-Review Professor (via `meeting --scope review`) |
| Code needs to be written | Graduate Student | Implementation Agent |
| Code needs to be run and verified | Graduate Student | Scientific Validator |
| After Scientific Validator completes | Graduate Student | Cache-Log Auditor |
| Publication-quality figures needed | Graduate Student | Implementation Agent |
| Workflow state changed | (automatic) | Cartographer (hook fires) |

### Parallel Task Spawning Rule

**One seed task = one Graduate Student.** This is a 1:1 mapping. Never collapse multiple tasks into a single Graduate Student; never split a single task across multiple Graduate Students.

**Graduate Students are not specialized by task type.** Every Graduate Student is a full-stack research executor with identical capabilities. There is no "baseline student", "scan student", "literature student", or "figure student". The student is bound to one task *instance* (e.g. "Task 3: reproduce Fig. 4 of Guo 2026") — not to a task *category*. Whatever sub-agents that task needs (Implementation Agent, Scientific Validator, Cache-Log Auditor), the same Graduate Student spawns them.

**Anti-pattern (forbidden):**

```
Lead Agent
    ├─ Graduate Student A  →  always does baseline work
    ├─ Graduate Student B  →  always does literature work
    └─ Graduate Student C  →  always does scan work
```

This is wrong for two reasons: (1) it implies role specialization that the harness does not define, and (2) it usually means the Lead Agent spawned them sequentially rather than in parallel.

**Correct pattern:**

```
Lead Agent
    │
    ├─ Graduate Student #1  →  Task 1 (reproduce baseline) ─┐
    ├─ Graduate Student #2  →  Task 2 (scan ε grid)         ├─ all spawned in a
    └─ Graduate Student #3  →  Task 3 (compute order param) ─┘  single message
                                                                with three parallel
                                                                Agent() calls
```

Each `#N` is a distinct ephemeral agent instance, not a person with a specialty. All three have the same skill load (`skills/graduate-student/SKILL.md`) and the same authority to spawn Implementation Agent / Scientific Validator / Cache-Log Auditor as their individual task requires.

**How to spawn in parallel:** when the dependency map in `seed_design.md` shows tasks with no inbound dependency on each other, the Lead Agent must issue them in **one assistant message containing multiple `Agent()` tool calls**. Sequential `Agent()` calls across multiple messages defeat the parallelism even when no dependency exists.

A task with `depends_on: [Task 1]` is spawned only after Task 1's Graduate Student reports back. A task with `depends_on: []` is spawned in the same parallel batch as every other independent task.

### Agent Model Hierarchy

Spawn each spawned tier with the appropriate model to balance quality and cost. The Lead Agent runs in whatever model the researcher chose for the main session; the table below applies only to spawned subagents.

| Tier | Role | Recommended model | Reason |
|---|---|---|---|
| Lead Agent | Main context | (session default) | Holds dialogue + judgment; not spawned |
| Graduate Student | Task execution + sub-agent coordination | `model: "sonnet"` | Reads papers, interprets physics, escalates anomalies |
| Implementation Agent | Code writing only | `model: "haiku"` | Spec is fully defined; no physical judgment needed |
| Scientific Validator | Run code + check criteria | `model: "sonnet"` | Must correctly apply pass/fail criteria |
| Cache-Log Auditor | Log/cache verification | `model: "haiku"` | Mechanical checklist; no interpretation |
| Peer-Review Professor | Adversarial review | `model: "sonnet"` or higher | Must produce substantive critique |

**Run-level override**: create `config/agent_models.yaml` in the run directory to override defaults per role. The Lead Agent reads this file before spawning agents. See `scripts/templates/agent_models.yaml` for the template.

### Role Agent Definitions And Tools

Claude Code loads `.claude/agents/<role>.md` for the selected `subagent_type` and applies that file's `tools:` frontmatter at runtime. The harness records the same role contract in `docs/harness/spawn_contracts.json`; `python scripts/check_spawn_contracts.py --project <project-dir>` is the offline consistency gate that verifies the agent file, skill declaration, tools list, allowed child `subagent_type` values, and description hygiene agree. It is not a substitute for runtime tool isolation.

Every role-agent description must start with `Explicitly spawned only` and must not contain auto-trigger examples such as "Use this agent when" or "Trigger when". This reduces opportunistic auto-delegation; it is a hygiene rule, not a hard runtime firewall.

| Role | `subagent_type` | Agent tools | Static scope |
|---|---|---|---|
| Graduate Student | `graduate-student` | `Read, Grep, Glob, Write, Edit, Agent` | writes only task evidence under `docs/evidence/`; may spawn only `implementation-agent`, `scientific-validator`, `cache-log-auditor` |
| Implementation Agent | `implementation-agent` | `Read, Write, Edit, Grep, Glob` | writes code/figure files from a precise spec; no code execution or claim judgment |
| Scientific Validator | `scientific-validator` | `Read, Grep, Glob, Bash` | runs validation commands and reports exact values; no Write/Edit |
| Cache-Log Auditor | `cache-log-auditor` | `Read, Grep, Glob, Bash` | runs audit commands and reports artifact sufficiency; no Write/Edit |
| Peer-Review Professor | `peer-review-professor` | `Read, Grep, Glob` | reads shared artifacts only; invoked only inside `meeting --scope review/full` |

### Spawn Block Templates

Every spawn block carries only what the *parent* knows that the child does not: the role label, the load instruction, and the run-specific inputs. Constraints, prohibitions, and report formats are owned by each role's `skills/<role>/SKILL.md` — do not duplicate them in the spawn prompt.

#### Graduate Student

Use `model: "sonnet"` and `subagent_type: graduate-student`.

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
| Graduate Student | **Writing or patching code** (must re-spawn Implementation Agent for every change); deciding claim ceiling; approving waivers; promoting claims beyond criteria |
| Lead Agent | Writing implementation code directly (must spawn Implementation Agent through Graduate Student); skipping Graduate Student tier and spawning Coding Subagents directly |
| Any Coding Subagent | Strengthening claim language without Lead Agent approval |

## Live Linked Research Graph

The Cartographer automation must maintain a **Live Linked Research Graph**, not just a static loop diagram. The Lead Agent, Graduate Test-Design Agents, and Coding Subagents emit `cartographer-update` packets when progress or evidence changes; PreToolUse/PostToolUse hooks supplement these with automatic activity records. The graph should expose Code links, Result links, and Interpretation links for every important node when those artifacts exist.

Live graph records must include:

- **Link Status**: `fresh`, `stale`, `missing`, `broken`, `pending_review`, or `superseded`.
- **Evidence Strength**: `none`, `weak`, `moderate`, `strong`, or `contradictory`, supplied by the Lead Agent rather than inferred by the Cartographer automation.
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

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Lead Agent must convene a completion conference summarizing all spawned agents' reports: Graduate Students, Coding Subagents, and the latest Cartographer state. The final report to the user must summarize the meeting, the workflow state, the visualization materials, evidence links, supported claims, unsupported claims, validation status, and remaining uncertainty.
