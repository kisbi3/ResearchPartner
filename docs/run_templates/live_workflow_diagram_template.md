# Live Workflow Diagram Template

Use this file as the Cartographer (hook-driven, not spawned)'s live artifact for a substantial research run.

The Cartographer (hook-driven, not spawned) listens to the Lead Agent, Graduate Test-Design Agents, and Coding Subagents. It does not give project opinions, infer mechanisms, judge scientific meaning, or strengthen claims. This artifact records process state only.

## Active Step

- Current step:
- Current owner:
- Last update:

## Workflow Diagram

Node labels show gate status emoji as they update: 🔄 in_progress · ✓ pass · ◑ partial · ❌ fail · ⛔ blocked · ⚠ waived

```mermaid
flowchart LR
    O["Orient"] --> I["Interview"]
    I --> SP["Specify"]
    SP --> L["Literature\nReplanning"]
    L --> SP
    L --> S["Seed / Stage 1"]
    S --> V["Stage 2\nSynthetic"]
    V --> E["Stage 3\nReal Data"]
    E --> EV["Stage 4\nMechanism"]
    EV --> R["Retrospective"]
    R --> RT["User Report"]
```

## Gate Status

| Gate | Status | Note |
|---|---|---|
| Professor interview | pending |  |
| Literature review and replanning | pending |  |
| Test-design seed | pending |  |
| Baseline or reproduction target | pending |  |
| Execution | pending |  |
| Visualization | pending |  |
| Professor evaluation | pending |  |
| Completion conference | pending |  |
| User report | pending |  |

Allowed status values: `pending`, `in_progress` 🔄, `pass` ✓, `partial` ◑, `fail` ❌, `blocked` ⛔, `waived` ⚠.

Update gate status in real time with:
```
python scripts/update_workflow_diagram.py --event start --step "..." --agent "..." --gate "Gate Name" --gate-status in_progress
```

## Evidence Links

- `docs/research_plan.md`
- `docs/literature_review_plan.md`
- `docs/paper_request_queue.md`
- `docs/replanning_memo.md`
- `literature/index.md`
- `literature/reviews/`
- `literature/extracted_text/`
- `docs/baseline_registry.md`
- `docs/validation_log.md`
- `docs/researcher_review_log.md`
- `docs/research_retrospective.md`

## Cartographer Update Events

Agents should send small update packets here whenever their work changes workflow state. The Cartographer (hook-driven, not spawned) records these packets as live linked research graph nodes. It must not infer scientific meaning or strengthen claims.

The allowed node types, relations, link-status values, evidence-strength values, and claim-ceiling values are defined once in [`docs/orchestration_protocol.md`](../../../docs/orchestration_protocol.md#live-linked-research-graph) — do not duplicate the enums here. Use `requires_researcher_review: true` as the Researcher Checkpoint Marker when the researcher should inspect a result, waiver, anomaly, or claim before the next step.

Use `preview: thumbnail`, `preview: table_head`, or `preview: log_tail` as the Artifact Preview hint when the workflow map should show or summarize an artifact.

```json
{
  "cartographer_update": {
    "from": "coding-subagent",
    "event_type": "figure",
    "node_id": "example-figure-node",
    "title": "Example Figure Node",
    "node_type": "figure",
    "summary": "Replace this with the observed workflow update.",
    "status": "pending_review",
    "link_status": "pending_review",
    "evidence_strength": "none",
    "claim_ceiling": "observation",
    "review_owner": "lead-agent",
    "requires_researcher_review": true,
    "code_links": [
      {
        "path": "scripts/example.py",
        "line": 1,
        "role": "replace with exact code role",
        "relation": "generates_figure",
        "status": "pending_review"
      }
    ],
    "result_links": [
      {
        "path": "outputs/example.png",
        "kind": "figure",
        "relation": "generated_by",
        "status": "pending_review",
        "preview": "thumbnail"
      }
    ],
    "interpretation_links": [
      {
        "path": "docs/validation_log.md",
        "anchor": "example",
        "relation": "documents_uncertainty",
        "status": "pending_review"
      }
    ],
    "graph_links": [
      {
        "from": "example-run-node",
        "to": "example-figure-node",
        "relation": "generated_by",
        "status": "pending_review"
      }
    ]
  }
}
```

## Blocked Behaviors

- No scientific claim is supported by this workflow diagram alone.
- Do not treat visualization as quantitative validation.
- Do not accept reproduction without comparing against the intended target.
- Do not let coding subagents strengthen claim language.

## Next Review Checkpoint

- Researcher decision needed:
- Question to ask:
- Smallest useful next action:

## In-Flight Tasks

<!-- Auto-updated by scripts/update_workflow_diagram.py via --event spawn / complete / error / resume.
     Rows in `spawned` state at session start are candidate abandoned tasks
     that the Professor Orchestrator must resolve before resuming. -->

| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |
|---|---|---|---|---|---|

Allowed in-flight status values: `spawned`, `acknowledged`, `abandoned`.

Before spawning a sub-agent via `Agent()`, log the spawn so a future session
can detect it if this session is cut off:

```
python scripts/update_workflow_diagram.py --event spawn \
    --step "..." --agent "graduate-student" \
    --task-id "task-3-reproduce-guo" \
    --evidence-record "docs/gates/seed_design.md#task-3"
```

When the sub-agent reports back, mark the row acknowledged:

```
python scripts/update_workflow_diagram.py --event complete \
    --step "..." --agent "graduate-student" --task-id "task-3-reproduce-guo"
```

After a session interruption, run `python scripts/check_session_resumable.py`
to list any rows still in `spawned` state.

## Real-Time Event Log

<!-- Auto-updated by scripts/update_workflow_diagram.py via PreToolUse/PostToolUse hooks -->

