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
- A waiver is issued by the Lead Agent

## Update Fields

For each update, record:

1. **Timestamp**: ISO date or session marker.
2. **Agent**: which role is sending this update (Lead Agent / Graduate Test-Design Agent / Coding Subagent / Cartographer).
3. **Active step**: the current loop phase.
4. **Gate change**: which gate changed and to what status — `open`, `blocked`, `waived`, or `passed`.
5. **Evidence link**: new or changed link (code / result / interpretation); include file path and link status (`fresh`, `stale`, `missing`, `broken`, `pending_review`, `superseded`).
6. **Claim ceiling**: `observation`, `interpretation`, `mechanism`, `generalization`, or `unsupported`.
7. **Staleness propagation**: list any artifacts that become stale as a result of this change.
8. **Researcher checkpoint**: whether the researcher must review before progress continues, and what they must inspect.

## Waiver Persistence Rule

Waivers must never be silent. Every waiver recorded in `seed-design`, `baseline-validation`, or any other skill must appear in the live workflow graph as a persistent node until the gate it bypassed is either:

- formally validated and the waiver closed by the Lead Agent, or
- explicitly acknowledged by the researcher as permanent.

A waiver node must carry all of the following:

- Gate bypassed
- Reason for waiver
- Risk remaining
- Claim ceiling imposed by the waiver
- Required follow-up validation

The Lead Agent, not the Cartographer, determines when a waiver may be closed. A closed waiver must still appear in the historical record.

## Staleness Propagation Rules

When code, data, parameters, units, analysis, or plotting change:

1. Mark all figures that depend on the changed artifact as `stale`.
2. Mark all captions, tables, and manuscript sections that reference those figures as `stale`.
3. Mark all interpretation links and claim-to-evidence entries that depend on those artifacts as `pending_review`.
4. Lower the overall claim ceiling to `observation` until the Lead Agent reviews and upgrades it.

Do not resolve staleness automatically. Only the Lead Agent can move a `stale` artifact to `fresh` after verifying or regenerating it.

## Gate Enforcement Record

When a gate blocks progress (rather than being waived), record:

- Which gate blocked
- Why it blocked (what was missing)
- What the researcher or Lead Agent must provide to unblock

Do not unblock a gate without explicit Lead Agent authorization. Unresolved blocks must remain visible in the live graph as open issue nodes.

## Auto-emission for Signal Artifacts

`scripts/workflow_hooks.py` automatically pushes a lineage node into `workflow_map.live.json` (and appends an event line to `docs/live_workflow_diagram.md`) whenever any of these files are written or edited inside a run directory:

| Path glob | Auto-derived fields |
|---|---|
| `docs/model_versions/<id>.md`     | `lineage_kind=model_version`, `model_version=<id>`, `node_type=model` |
| `literature/reviews/<paper_id>.md`| `lineage_kind=paper`, `paper_id=<paper_id>`, `node_type=paper` |
| `docs/claims/<claim_id>.md`       | `lineage_kind=claim`, `node_type=claim`, `requires_researcher_review=true` |
| `outputs/figures/*.png|pdf|svg|jpg` | `lineage_kind=figure`, `thumbnail_path=<rel>`, `node_type=figure` |
| `errors/*.err`                    | `lineage_kind=anomaly`, `node_type=anomaly`, `status=blocked` |

The hook only seeds the node. **Cross-referential edges** — `evolved_from` between model versions, `reproduces` from a result to a paper, `cites_paper` from a decision or claim to a paper — must still be added by an explicit cartographer-update call (the filesystem can't see them).

When working with these artifacts, **write the file first** (the hook auto-creates the node), then issue a follow-up cartographer-update **only** to add edges or to override an auto-derived field. Do not re-emit the node fields the hook already filled in.

## Live Workflow Artifact

**Primary (machine path):** call `python scripts/update_live_json.py` to push state directly into `workflow_map.live.json`. The HTML polls this file every 10 seconds, so the researcher's browser updates automatically with no manual regeneration step.

```bash
# Gate status update
python scripts/update_live_json.py --run <run-dir> \
    --gate "<gate name>" --status <pass|fail|partial|blocked|waived|pending> \
    --note "<short note>"

# Active-step banner only
python scripts/update_live_json.py --run <run-dir> \
    --active-step "<current phase description>"

# Full cartographer event packet (use when code/result/interpretation links matter)
python scripts/update_live_json.py --run <run-dir> \
    --event '{"cartographer_update": {"node_id": "...", "title": "...", "status": "passed", ...}}'

# Also refresh the central docs/workflow_map.live.json
python scripts/update_live_json.py --run <run-dir> \
    --gate "Stage 2" --status pass --note "13 models done" --update-central
```

**Secondary (human log):** also update `docs/process/live_workflow_diagram.md` — the Gate Status table, Active Step, and Next Review Checkpoint sections — so the Markdown file stays readable as a research record. This step is for human auditability; the HTML does not depend on it.

If the run directory has no `workflow_map.live.json` yet, call `update_live_json.py` with any flag and it will bootstrap one from the current run state.

If neither the script nor the run directory is available, produce the update as a structured log entry:

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

## Worked Examples by Lineage Kind

These examples cover the cases where the agent must explicitly emit a node or an edge — i.e. anything beyond what the workflow_hooks auto-emit handles.

### Paper node + cites_paper edge (decision references a paper)

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "decision_use_lacasa_method",
    "title": "Adopt HVG method from Lacasa 2008",
    "node_type": "decision",
    "lineage_kind": "decision",
    "summary": "Use horizontal visibility graph as primary mapping.",
    "graph_links": [
      {"from": "decision_use_lacasa_method", "to": "paper_lacasa2008",
       "relation": "cites_paper", "status": "fresh"}
    ]
  }
}'
```

### Model version evolution (v2 evolved_from v1)

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "model_v2",
    "title": "Model v2 with damping term",
    "node_type": "model",
    "lineage_kind": "model_version",
    "model_version": "v2",
    "summary": "Added linear damping to v1 equations of motion.",
    "graph_links": [
      {"from": "model_v2", "to": "model_v1",
       "relation": "evolved_from", "status": "fresh"}
    ]
  }
}'
```

### Result reproduces a paper figure

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "result_baseline_fig3",
    "title": "Reproduced Lacasa 2008 Fig. 3",
    "node_type": "validation",
    "lineage_kind": "result",
    "evidence_strength": "strong",
    "summary": "HVG degree distribution matches Fig. 3 (chi2 p=0.42).",
    "graph_links": [
      {"from": "result_baseline_fig3", "to": "paper_lacasa2008",
       "relation": "reproduces", "status": "fresh"}
    ]
  }
}'
```

### Cross-run lineage (current run derived from a prior one)

```bash
python scripts/update_live_json.py --run "$RUN" --event '{
  "cartographer_update": {
    "from": "lead-agent",
    "node_id": "model_v1",
    "title": "Model v1 (carried over from prior run)",
    "node_type": "model",
    "lineage_kind": "model_version",
    "model_version": "v1",
    "parent_run": "ResearchPartner-runs/2026-05-10-hvg-baseline",
    "summary": "Reusing validated v1 from prior baseline run."
  }
}'
```

`parent_run` is what the **Cross-Run Lineage** tab uses to draw an edge from this node to its ancestor run. Set it whenever a node materially carries forward from another run (a model version, a validated result, a paper review).

### Quick reference: when to use each new relation

| `graph_links.relation` | Use when |
|---|---|
| `evolved_from` | model_version B is a successor of model_version A |
| `reproduces`   | a `result` confirms a target — typically a `paper` figure/equation, or a prior validated result |
| `cites_paper`  | a `decision`, `claim`, or `result` is directly justified by a specific `paper` node |

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
