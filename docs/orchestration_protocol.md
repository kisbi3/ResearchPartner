# Orchestration Protocol — Professor-Led Lab (Single-Spawner) + Leaf Agents

This document holds the multi-agent orchestration mechanics (role definitions, agent spawning protocol, spawn-block templates, live research graph rules, professor stances, completion conference). It is referenced from `AGENTS.md` / `GEMINI.md` so that subagents (Graduate Student, Code Reviewer, Scientific Validator, Cache-Log Auditor, Workflow Manager, Peer-Review Professor) do not have to load these rules — they receive their role-specific instructions through their spawn block and their own `.claude/agents/<role>.md` definition plus `skills/<role>/SKILL.md`.

**Who loads this file**

- **Always**: Lead Agent (main session) — load explicitly at the start of any substantial research iteration.
- **Never required**: the leaf agents (Graduate Student, Code Reviewer, Scientific Validator, Cache-Log Auditor, Workflow Manager, Peer-Review Professor) — their behavior is fully specified by their spawn block + their `.claude/agents/<role>.md` definition + their `skills/<role>/SKILL.md`.

## The lab

Model the work as a research group. The PI (the human researcher) sets direction and owns the decisions; the Lead Agent is the professor who runs the group; the spawned agents are the lab members.

- **PI (human)** — not an agent. Owns the science and the gate decisions. The brake: the researcher-owned decision files (`docs/gates/{orient,interview,model,seed}_decision.md`, plus the skip waivers) are write-blocked for *every* agent, so the lab can propose but never sign its own approval. See `docs/hooks_reference.md`.
- **Lead Agent — the professor** (the main conversation context, *not* a spawned agent): owns scientific judgment, assumptions, model meaning, validation gates, evidence sufficiency, reproduction fidelity, and final claim discipline. The only role with two-way dialogue with the PI and the **only spawner**. Holds the professor stances (Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, Architect) across Orient → Interview → Specify → Evaluate → Review. Discusses results *with* the graduate students.
- **Graduate Student** (spawned leaf; may run in parallel): a junior researcher for one bounded task. Proposes an approach, writes and runs code under `src/`, records evidence, and reports its interpretation **as hypotheses** plus open questions. Does not pronounce the binding verdict, promote claims, sign decisions, or spawn. Load `skills/graduate-student/SKILL.md`.
- **Code Reviewer** (spawned leaf; may run in parallel): reads a graduate student's code **statically** (no execution) and judges correctness, spec conformance, and reproducibility hygiene. Load `skills/code-reviewer/SKILL.md`.
- **Scientific Validator** (spawned leaf): **independently re-runs** the code via `run_with_capture.py` and pronounces PASS/FAIL against the pre-set criterion — mechanically, no interpretation. This is the disinterested referee. Load `skills/scientific-validator/SKILL.md`.
- **Cache-Log Auditor** (spawned leaf): audits the validated run's logs/errors/cache artifacts mechanically. Load `skills/cache-log-auditor/SKILL.md`.
- **Workflow Manager** (spawned leaf): runs `scripts/sync_workflow.py`, refreshes the live workflow diagram + JSON, and reports gate status and broken lineage edges. Load `skills/workflow-manager/SKILL.md`.
- **Peer-Review Professor** (spawned leaf, `meeting --scope review`/`full` only): adversarial external reviewer with no project history; reads only what is explicitly shared. Load `skills/peer-review-professor/SKILL.md`. Single-shot critique, then done.

### The integrity principle: author ≠ validator

The graduate student that writes and runs code is the **author**. The author may interpret its own result, but only as a hypothesis. The binding pass/fail verdict is pronounced by a **different** agent (the Scientific Validator) re-running independently against a criterion the PI locked at the model/seed gate. Code review (is the code right?), behavioural validation (does the result meet the bar?), and artifact audit (are the run's artifacts clean?) are three separate, single-responsibility leaf agents. No agent certifies its own work; the PI's gate sits on top.

## Agent Spawning Protocol

The Lead Agent (professor) is the only spawner. Live testing showed spawned subagents do not receive the `Agent` tool, so nested spawning is not part of the harness contract. Leaf roles are enforced by actually spawning separate agents using the `Agent()` tool with explicit `subagent_type` values.

### Single-Spawner Hierarchy

```
Lead Agent — professor (main context — not spawned)
    │   owns: dialogue with the PI, scientific judgment, gate approval,
    │          claim ceiling, professor stances, task breakdown
    │
    ├─ Graduate Student        ← spawned per task; writes + runs code; may run in PARALLEL
    │       reports evidence + hypotheses; no binding verdict, promotion, or spawning
    │
    ├─ Code Reviewer           ← spawned to review a student's code STATICALLY (no run)
    │       reports correctness / spec / reproducibility issues; may run in parallel
    │
    ├─ Scientific Validator    ← spawned to RE-RUN and check the pre-set criterion
    │       independent PASS/FAIL; does NOT modify code, spawn, or interpret
    │
    ├─ Cache-Log Auditor       ← spawned after the Validator
    │       audits logs/ errors/ cache/ mechanically; no interpretation
    │
    ├─ Workflow Manager        ← spawned to refresh workflow + lineage state
    │       runs sync_workflow.py; reports gate status; no research code
    │
    └─ Peer-Review Professor   ← spawned only in meeting --scope review/full
            single-shot adversarial critique; reads shared artifacts; done
```

### When to Spawn

| Situation | Who spawns | What to spawn |
|---|---|---|
| A bounded research/seed task is ready | Lead Agent | `graduate-student` (one per task; issue several in one message for parallel, independent tasks) |
| A student's code is ready to review | Lead Agent | `code-reviewer` (static review) |
| Reviewed code must be run and checked against the criterion | Lead Agent | `scientific-validator` |
| After the Scientific Validator completes | Lead Agent | `cache-log-auditor` |
| Workflow / lineage state needs a refresh | Lead Agent | `workflow-manager` (or `/sync-workflow`) |
| Adversarial review before promoting a claim | Lead Agent | `peer-review-professor` (via `meeting --scope review`) |

### Parallel Task Coordination Rule

**Graduate students run in parallel.** When the dependency map in `seed_design.md` shows tasks with no inbound dependency on each other, the Lead Agent issues several `graduate-student` spawns in one assistant message — one `subagent_type: graduate-student` call per task. Each student stays strictly inside its own task and its own files.

A task with `depends_on: [Task 1]` begins only after Task 1's evidence and the Lead's decision are recorded. Code Reviewers may likewise be spawned in parallel across finished students. The Scientific Validator and Cache-Log Auditor run per validated artifact.

**Correct pattern:**

```
Lead Agent (professor)
    ├─ Task 1 → graduate-student → code-reviewer → scientific-validator → cache-log-auditor
    ├─ Task 2 → graduate-student → code-reviewer → scientific-validator → cache-log-auditor
    └─ Task 3 → graduate-student → …                       (Tasks 1–3 spawned in parallel)
```

The professor then convenes, discusses the hypotheses with the students, and brings the proposal to the PI at the gate.

### Agent Model Hierarchy

Spawn each tier with the appropriate model to balance quality and cost. The Lead Agent runs in whatever model the researcher chose for the main session; the table below applies only to spawned subagents.

| Tier | Role | Recommended model | Reason |
|---|---|---|---|
| Lead Agent | Main context (professor) | (session default) | Holds dialogue + judgment; not spawned |
| Graduate Student | Leaf: write + run + interpret | `model: "sonnet"` | Needs research judgment, not just transcription |
| Code Reviewer | Leaf: static code review | `model: "sonnet"` | Must catch real correctness/spec defects |
| Scientific Validator | Leaf: run + check criteria | `model: "sonnet"` | Must apply pass/fail criteria exactly |
| Cache-Log Auditor | Leaf: log/cache verification | `model: "haiku"` | Mechanical checklist; no interpretation |
| Workflow Manager | Leaf: workflow refresh | `model: "haiku"` | Deterministic refresh + reporting |
| Peer-Review Professor | Leaf: adversarial review | `model: "sonnet"` or higher | Must produce substantive critique |

### Role Agent Definitions And Tools

Claude Code loads `.claude/agents/<role>.md` for the selected leaf `subagent_type` and applies that file's `tools:` frontmatter at runtime. The harness records the same leaf-role contract in `docs/harness/spawn_contracts.json`; `python scripts/check_spawn_contracts.py --project <project-dir>` is the offline consistency gate that verifies the agent file, skill declaration, tools list, empty child-spawn declarations, and description hygiene agree. It is not a substitute for runtime tool isolation.

Every role-agent description must start with `Explicitly spawned only` and must not contain auto-trigger examples such as "Use this agent when" or "Trigger when". This reduces opportunistic auto-delegation; it is a hygiene rule, not a hard runtime firewall.

The `Agent` tool is reserved for the Lead Agent. No `.claude/agents/<role>.md` leaf definition may list `Agent` in `tools:`, and no leaf role may declare child `subagent_type` values.

| Role | `subagent_type` | Agent tools | Static scope |
|---|---|---|---|
| Graduate Student | `graduate-student` | `Read, Write, Edit, Grep, Glob, Bash` | writes + runs code for one task; reports evidence + hypotheses; no binding verdict, claim promotion, or spawning; parallel |
| Code Reviewer | `code-reviewer` | `Read, Grep, Glob` | static code review (no execution); reports correctness/spec/reproducibility issues; no verdict or spawning |
| Scientific Validator | `scientific-validator` | `Read, Grep, Glob, Bash` | independent re-run + pass/fail verdict against pre-set criteria; no Write/Edit or spawning |
| Cache-Log Auditor | `cache-log-auditor` | `Read, Grep, Glob, Bash` | audits run cache/logs/artifacts; no interpretation or spawning |
| Workflow Manager | `workflow-manager` | `Read, Grep, Glob, Bash` | refreshes workflow/lineage state; no research code, runs, or interpretation |
| Peer-Review Professor | `peer-review-professor` | `Read, Grep, Glob` | reads shared artifacts only; invoked only inside `meeting --scope review/full` |

### Leaf Spawn Block Templates

Every leaf spawn block carries only what the Lead knows that the child does not: the role label, the load instruction, and the run-specific inputs. Constraints, prohibitions, and report formats are owned by each role's `.claude/agents/<role>.md` and `skills/<role>/SKILL.md` — do not duplicate them in the spawn prompt.

#### Graduate Student

Use `model: "sonnet"` and `subagent_type: graduate-student`. Issue several in one message for parallel, independent tasks.

```
You are a Graduate Student.
Load skills/graduate-student/SKILL.md — it defines your role, constraints,
and report format.

Project root: <absolute path>
Task: <copy the exact task block from seed_design.md>
Write to: src/<filename>.py
Pass criterion: <exact criterion — recorded for the Scientific Validator, not for you to pronounce>
Evidence record: docs/evidence/<file>
On ambiguity: apply the most conservative reading and flag it.
```

#### Code Reviewer

Use `model: "sonnet"` and `subagent_type: code-reviewer`. May be spawned in parallel across finished students.

```
You are a Code Reviewer.
Load skills/code-reviewer/SKILL.md — it defines your static review checklist
and report format.

Project root: <absolute path>
Review: src/<filename>.py
Against spec: docs/plan/model_spec.md  (and the task block)
```

#### Scientific Validator

Use `model: "sonnet"` and `subagent_type: scientific-validator`.

```
You are a Scientific Validator.
Load skills/scientific-validator/SKILL.md — it defines your role, constraints,
and report format.

Project root: <absolute path>
Script to validate: src/<filename>.py
Run command: python scripts/run_with_capture.py --quiet <project_dir> src/<filename>.py [args]
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

Project root: <absolute path>
Script stem: <filename without .py>
Log path: <log file path from Scientific Validator's report>
Expected cache files (relative to project_dir):
  - <cache/filename1.npy>   ← omit section if no cache files are required
Min numeric lines: <N>      ← default 3 if not specified in task

Run: python scripts/audit_run_outputs.py <project_dir> <stem> --log <log_path> \
     [--expect-cache <rel_path> ...] [--min-numeric <N>]
Evidence record: docs/gates/validation_log.md
```

#### Workflow Manager

Use `model: "haiku"` and `subagent_type: workflow-manager`.

```
You are a Workflow Manager.
Load skills/workflow-manager/SKILL.md — it defines your refresh + report format.

Project root: <absolute path>
Run: python scripts/sync_workflow.py
Report: gate status (note any gate blocked on a PI decision file) and broken lineage edges.
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
| Graduate Student | Pronouncing the binding pass/fail verdict (that is the Scientific Validator); promoting claims past `observation`; writing a gate decision/waiver; spawning agents |
| Code Reviewer | Running code; applying pass/fail criteria; modifying code; spawning agents |
| Scientific Validator | Modifying code; inventing new criteria; interpreting physical meaning; spawning agents |
| Cache-Log Auditor | Running research scripts; interpreting scientific content; deciding whether to retry; spawning agents |
| Workflow Manager | Writing/running research code; interpreting results; authoring gate artifacts; spawning agents |
| Lead Agent (professor) | Writing or signing any researcher-owned decision file (the brake — PI only); strengthening a claim past the validated evidence |
| Any leaf agent | Spawning agents; strengthening claim language without Lead Agent approval |

## Live Linked Research Graph

The workflow automation maintains a **Live Linked Research Graph**, not just a static loop diagram. The Lead Agent and leaf agents leave evidence and lineage records when progress changes; `workflow_hooks.py` supplements these with automatic Agent activity records, and `/sync-workflow` (or the Workflow Manager) rebuilds the visible state. The graph should expose Code links, Result links, and Interpretation links for every important node when those artifacts exist.

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

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Lead Agent convenes a completion conference summarizing all leaf-agent reports (graduate-student evidence + hypotheses, code-review verdicts, validator verdicts, auditor verdicts) and the latest workflow state. The final report to the PI must summarize the meeting, the workflow state, the visualization materials, evidence links, supported claims, unsupported claims, validation status, and remaining uncertainty — and, where a gate decision is due, present the proposal for the PI to record in the researcher-owned decision file.
