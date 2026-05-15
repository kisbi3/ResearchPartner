---
name: cartographer-update
description: Use when the active research step changes, a gate passes or blocks, an evidence link is added or broken, a waiver is recorded, an artifact becomes stale, or the next researcher review checkpoint changes. Updates the live workflow artifact without strengthening claims or inferring scientific meaning.
---

# Cartographer Update Skill

Use this skill whenever the live workflow state changes. The Cartographer records process state only — it does not judge scientific meaning, infer mechanisms, or strengthen claims.

## When to Invoke

Invoke this skill when any of the following occurs:

- The active loop phase changes (Orient → Interview → Specify → Seed → Validate → Execute → Evaluate → Review → Retrospect)
- A gate passes, blocks, or is waived
- An evidence link is added, confirmed fresh, or found broken or stale
- A baseline, validation, or reproduction result is recorded
- A figure, table, or artifact is generated or invalidated
- A researcher review checkpoint is reached or cleared
- A claim ceiling is established or revised
- A prohibited behavior is avoided (gate enforced)
- An anomaly is logged
- A completion conference is held
- A waiver is issued by the Professor Orchestrator

## Update Fields

For each update, record:

1. **Timestamp**: ISO date or session marker.
2. **Agent**: which role is sending this update (Professor Orchestrator / Graduate Test-Design Agent / Coding Subagent / Cartographer).
3. **Active step**: the current loop phase.
4. **Gate change**: which gate changed and to what status — `open`, `blocked`, `waived`, or `passed`.
5. **Evidence link**: new or changed link (code / result / interpretation); include file path and link status (`fresh`, `stale`, `missing`, `broken`, `pending_review`, `superseded`).
6. **Claim ceiling**: `observation`, `interpretation`, `mechanism`, `generalization`, or `unsupported`.
7. **Staleness propagation**: list any artifacts that become stale as a result of this change.
8. **Researcher checkpoint**: whether the researcher must review before progress continues, and what they must inspect.

## Waiver Persistence Rule

Waivers must never be silent. Every waiver recorded in `seed-design`, `baseline-validation`, or any other skill must appear in the live workflow graph as a persistent node until the gate it bypassed is either:

- formally validated and the waiver closed by the Professor Orchestrator, or
- explicitly acknowledged by the researcher as permanent.

A waiver node must carry all of the following:

- Gate bypassed
- Reason for waiver
- Risk remaining
- Claim ceiling imposed by the waiver
- Required follow-up validation

The Professor Orchestrator, not the Cartographer, determines when a waiver may be closed. A closed waiver must still appear in the historical record.

## Staleness Propagation Rules

When code, data, parameters, units, analysis, or plotting change:

1. Mark all figures that depend on the changed artifact as `stale`.
2. Mark all captions, tables, and manuscript sections that reference those figures as `stale`.
3. Mark all interpretation links and claim-to-evidence entries that depend on those artifacts as `pending_review`.
4. Lower the overall claim ceiling to `observation` until the Professor Orchestrator reviews and upgrades it.

Do not resolve staleness automatically. Only the Professor Orchestrator can move a `stale` artifact to `fresh` after verifying or regenerating it.

## Gate Enforcement Record

When a gate blocks progress (rather than being waived), record:

- Which gate blocked
- Why it blocked (what was missing)
- What the researcher or Professor Orchestrator must provide to unblock

Do not unblock a gate without explicit Professor Orchestrator authorization. Unresolved blocks must remain visible in the live graph as open issue nodes.

## Live Workflow Artifact

Update `docs/run_templates/cartographer_update_template.md` or the run-local `docs/live_workflow_diagram.md` when available.

If neither file exists, produce the update as a structured log entry:

```
[Cartographer Update]
Timestamp:
Agent:
Active step:
Gate change:
Evidence link:
  - path:
  - status: fresh | stale | missing | broken | pending_review | superseded
  - type: code | result | interpretation
Claim ceiling:
Staleness:
  - (list stale artifacts)
Waiver nodes:
  - gate:
  - reason:
  - risk:
  - claim ceiling:
  - follow-up:
Researcher checkpoint:
```

## Output Format

### Workflow State

State the current active loop phase and the status of each gate that has been touched.

### Changes This Update

List each field that changed and its new value.

### Active Waivers

List all waivers that are still open, with their gate, risk, and claim ceiling.

### Stale Artifacts

List all artifacts currently marked `stale` or `pending_review`, with the reason each became stale.

### Next Researcher Checkpoint

State what the researcher must inspect before progress continues, and which gate or evidence link is blocking until they do.
