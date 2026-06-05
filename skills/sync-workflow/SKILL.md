---
name: sync-workflow
description: Refresh the live workflow diagram (workflow_map.live.json + live_workflow_diagram.md) by walking the project file system. On-demand only. Run when you want workflow_map.html to show the current research state, or when lineage edges have been added or changed.
---

# Sync Workflow

Refresh the project's live workflow artifact by diagnostic walk of the file system. This replaces the old hook-driven Cartographer system: there is no auto-update on Write/Edit any more. The diagram only changes when you call this skill (or when the Agent-spawn hook adds an in-flight row).

## When to Invoke

- The researcher wants to see the current workflow in `workflow_map.html`.
- You have just added or edited multiple gate, claim, model_version, paper, figure, or anomaly artifacts and want the dashboard to reflect them.
- You have added or changed `lineage:` front-matter in any artifact and want the new edges to render in the Lineage tab.
- The researcher asks to "update the workflow diagram", "refresh the dashboard", or types `/sync-workflow` directly.

Do NOT invoke after every single file edit. The skill is on-demand by design — micro-syncing defeats the purpose.

## How to Invoke

```bash
python scripts/sync_workflow.py [--project <project-dir>]
```

Defaults: walks up from cwd to find the `.research-harness` marker. Pass `--project <path>` to target a specific project.

Optional flags:

- `--active-step "Stage 2 — synthetic experiments"` — rewrite the *Active Step* banner. Without this, the existing banner is preserved (the Agent-spawn hook keeps it up to date for running sub-agent tasks).
- `--validate-edges` — after the sync, check every `graph_links` / `edges` reference resolves to a real node id. Exit 2 on any broken edge. Use this before promoting a claim ceiling or asking the researcher to review lineage.

## What It Does

The script is **pure deterministic walk** — no LLM, no sub-agent. Output is reproducible from the same filesystem inputs.

1. Walks the project's artifact directories:
   - `docs/gates/` → gate nodes (synthesised one per canonical gate, plus per-file detail nodes)
   - `docs/plan/` → plan/decision nodes
   - `docs/literature/` → literature-plan / replanning nodes
   - `docs/model_versions/` → model_version nodes
   - `literature/reviews/` → paper nodes
   - `docs/claims/` → claim nodes
   - `outputs/figures/` → figure nodes (with thumbnail path)
   - `docs/meetings/` → meeting decision nodes
   - `docs/checkpoints/` → stage-checkpoint decision nodes
   - `errors/` → anomaly nodes (status defaults to `blocked`)
   - Any file whose stem ends in `_waiver` is reclassified as a `waiver` node.

2. For each file, parses an optional `lineage:` YAML front-matter block (see *Front-matter spec* below) for cross-referential edges and status overrides.

3. Rewrites `<project>/workflow_map.live.json` from scratch.

4. Mirrors the inferred *Active Step* (only when `--active-step` is given) and *Gate Status* table into `<project>/docs/process/live_workflow_diagram.md`, **preserving**:
   - `## In-Flight Tasks` — maintained by the Agent-spawn hook.
   - `## Real-Time Event Log` — append-only history written by the spawn hook.
   - `## Evidence Links`, `## Blocked Behaviors`, `## Next Review Checkpoint` — human-managed sections.

5. `workflow_map.html` polls `workflow_map.live.json` every ~10 seconds, so the dashboard reflects the sync within one poll cycle. No manual refresh needed.

## Front-matter Spec

To draw lineage edges, add a YAML front-matter block to the top of any artifact file:

```yaml
---
lineage:
  node_type: claim                       # optional; overrides directory default
  status: passed                         # pending | in_progress | passed | blocked | waived | resolved
  first_model_version: true              # only for model_v1: marks the chain root (no evolved_from required)
  evolved_from: [model_v1]               # model_version chain
  reproduces: [paper_lacasa2008]         # this result reproduces a paper / baseline
  cites_paper: [paper_lacasa2008]        # this decision / claim cites a paper
  supports: [figure_baseline_match]      # this evidence supports a claim
  contradicts: [claim_universal_scaling] # …or contradicts it
  limits: [claim_universal_scaling]      # this anomaly limits the claim
  paper_id: lacasa2008                   # override the paper id (default = filename stem)
  model_version: v2                      # override the model version id
  evidence_strength: strong              # none | weak | moderate | strong
  claim_ceiling: mechanism               # unsupported | observation | interpretation | mechanism | generalization
---

# File body…
```

All keys are optional. A file without front-matter still appears as a node — it just has no outgoing edges and uses the directory default for `node_type`.

### Target id conventions

When you write `supports: [foo]`, the target id `foo` must match the node id sync-workflow generates for the target file. The pattern is `<type-prefix>_<file-stem-slug>`:

| File path | Generated node id |
|---|---|
| `docs/claims/c_universal_scaling.md` | `claim_c_universal_scaling` |
| `docs/model_versions/v1.md` | `model_v1` |
| `literature/reviews/lacasa2008.md` | `paper_lacasa2008` |
| `outputs/figures/fig_scaling.png` | `figure_fig_scaling` |
| `errors/run_42.err` | `anomaly_run_42` |
| `docs/meetings/2026-05-20-baseline-check.md` | `meeting_2026_05_20_baseline_check` |

The slug rule: lowercase, non-alphanumeric runs → `_`, strip leading/trailing `_`.

If your target lives outside the harness directory layout (an external paper id, a manually managed claim), set it explicitly: declare a node with that id in some artifact's front-matter via `id:`, or accept that the edge will show up in `--validate-edges` as broken.

## Status inference (when no front-matter)

If a file has no `lineage.status`, the script falls back to scanning the body for these patterns:

- `Status: <value>` or `Gate Status: <value>` or `Literature Gate Status: <value>` (case-insensitive)
- A `## Status` heading followed immediately by a status word

Recognised values map to phases via:

| Raw value | Phase |
|---|---|
| `pass`, `passed`, `complete`, `ready` | `passed` |
| `fail`, `failed`, `blocked`, `partial` | `blocked` |
| `waived` | `waived` |
| `in_progress`, `active` | `active` |
| `pending` (default) | `pending` |

If no marker is found, the phase stays `pending` (or `blocked` for error files).

## Gate Status table inference

The Gate Status table in the markdown mirror is rewritten from a fixed mapping of file stem → gate name:

| File stem | Gate name |
|---|---|
| `orient_note` | Orient gate |
| `interview_notes` | Interview gate |
| `literature_review_plan` | Literature review and replanning |
| `seed_design` | Test-design seed |
| `baseline_strategy`, `baseline_registry` | Baseline or reproduction target |
| `validation_log`, `execution_complete` | Execution |
| `visualization_complete` | Visualization |
| `professor_evaluation` | Professor evaluation |
| `research_retrospective` | Completion conference |
| `user_report` | User report |

When multiple files feed one gate, the strongest non-`pending` status wins. To force a specific gate to a specific status without editing a gate file, set `lineage.status` in front-matter on whichever file the table draws from.

### Adoption mode (brownfield)

When `docs/gates/adoption_decision.md` is PI-signed (the project is in **adoption mode**, see the `existing-research-onboarding` skill), the sync surfaces that state so the dashboard matches what `enforce_gate_sequence.py` already honours:

- An extra **`Adoption (brownfield)`** row is inserted after the Interview gate, shown as `pass` with the note *"PI-signed; model + baseline-strategy satisfied-by-adoption"*. Greenfield projects never get this row.
- The signed `adoption_decision.md` node is reported as `passed` (it has no `Status:` line, so without this it would read `pending`).
- The **`Baseline or reproduction target`** row keeps its real status (the reproduction is **not** waived by adoption) but gains the note *"strategy satisfied-by-adoption; reproduction still required"* — or *"… reproduction passed"* once the registry flips to `pass`. The status itself stays honest; only the note explains the satisfied-by-adoption semantics.

## What this skill does NOT do

- It does not invent edges. If `supports`, `evolved_from`, etc. are not declared in front-matter, they are not in the graph.
- It does not strengthen any claim. `claim_ceiling` reflects what the front-matter says.
- It does not run validation, simulate, or compute anything scientific.
- It does not delete files. Removing an artifact from disk removes its node on the next sync; nothing else.

## Companion: the Agent-spawn hook

`scripts/workflow_hooks.py` (registered on `PreToolUse:Agent` / `PostToolUse:Agent`) maintains the *In-Flight Tasks* table in real time:

- On `Agent()` spawn: append a row with status `spawned`, deterministic task id derived from the tool input.
- On `Agent()` completion or error: mark the row `acknowledged`.

This is the only thing that updates automatically. Everything else waits for sync-workflow.
