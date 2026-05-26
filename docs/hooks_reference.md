# Hooks Reference

Detailed descriptions of the harness's automated enforcement hooks. `AGENTS.md` / `GEMINI.md` link to this file rather than inlining the descriptions so the contract files stay compact (every spawned subagent that loads `AGENTS.md` pays for that prose). Soft "discipline" hooks (Numerical Stability, Anomaly, Scope Creep, etc.) stay inline in `AGENTS.md`; the entries here are the ones that involve a script, a hook registration, or an enforcement decision.

## Cross-Tier Write Hook (HARD ENFORCED)

Every `.py` or `.ipynb` file written anywhere under a `ResearchPartner-runs/<run>/` directory (except `<run>/docs/` and `<run>/literature/`) must come from a spawned Implementation Agent. The Lead Agent and Graduate Students are forbidden from writing code; Graduate Students *review* code and re-spawn the Implementation Agent for every correction.

- **Hook**: PreToolUse on `Write|Edit` → `scripts/check_src_write_authorization.py`
- **Decision**: allow iff `<run>/docs/gates/agent_spawn_log.md` has a matching `implementation` row for the target file, or was modified within the last 10 minutes.
- **Bypass**: `RESEARCH_HARNESS_BYPASS_SRC_GATE=1` for an explicit one-off waiver.

## Bash Code-Write Hook (HARD ENFORCED)

Closes the Bash bypass of the cross-tier write hook. Bash commands such as `echo … > sim.py`, `cat <<EOF > sim.py`, `sed -i … sim.py`, `cp other.py <run>/src/sim.py`, `python -c "open('sim.py', 'w')…"`, `Set-Content`, or `Out-File` would otherwise produce code without triggering Write/Edit.

- **Hook**: PreToolUse on `Bash|PowerShell` → `scripts/check_bash_code_write.py`
- **Decision**: block any command whose shell-write syntax (`>`, `>>`, `tee`, `sed -i`, `cp/mv/install/rsync`, heredoc redirect, `Set-Content`/`Out-File`/`Add-Content`, `python -c "open(…,'w')"`) targets a `.py`/`.ipynb` path inside a run directory (excluding `<run>/docs/` and `<run>/literature/`).
- **Bypass**: same `RESEARCH_HARNESS_BYPASS_SRC_GATE=1`.

## Cross-Tier Compliance Gate Hook

Backstop for the two write hooks above. Run before advancing a stage gate.

- **Script**: `python scripts/check_cross_tier_compliance.py --run <run-dir> [--strict]`
- **Decision**: exits 2 when `src/*.py` files exist without matching Implementation Agent spawn records. `--strict` also fails on missing spawn log.

## Spawn Log Integrity Hook

`docs/gates/agent_spawn_log.md` is plain Markdown — a forged row could let a direct code write pass the cross-tier hook. This script reconciles spawn-log rows against Agent() start events recorded automatically by `workflow_hooks.py` in `<run>/docs/live_workflow_diagram.md`.

- **Script**: `python scripts/check_spawn_log_integrity.py --run <run-dir>`
- **Decision**: exits 2 when, for any date bucket, the spawn log has more `implementation` rows than the diagram has Agent() `start` events whose description mentions "implementation".

## Claim Promotion Gate Hook (HARD ENFORCED)

Run before the Lead Agent promotes the run's claim ceiling above `observation`.

- **Script**: `python scripts/check_claim_promotion.py --run <run-dir> --target <observation|interpretation|mechanism|generalization>`
- **Input**: `<run>/docs/gates/validation_log.md` rows (`| Date | Check | Target | Status | Evidence |`).
- **Count gate**: interpretation ≥ 1 pass; mechanism ≥ 2 pass; generalization ≥ 3 pass.
- **Diversity gate**: `mechanism` requires ≥ 1 baseline-class pass (Check matching `toy_model | reproduction | analytical | conservation | dimensional | known_limit`). `generalization` requires ≥ 2 distinct Check categories.
- **Bypass**: lower the target ceiling or add a waivered validation row.

## Peer-Review Invocation Hook (HARD ENFORCED)

A Peer-Review Professor may only be spawned from within a `meeting --scope review` (or `--scope full`) session.

- **Hook**: PreToolUse on `Agent` → `scripts/check_peer_review_invocation.py`
- **Decision**: block when the spawn prompt names the Peer-Review role unless either (a) the same prompt references the `meeting` skill with `--scope review`/`--scope full`, or (b) a `<run>/docs/meetings/*.md` artifact was touched within the last 10 minutes.
- **Bypass**: `RESEARCH_HARNESS_BYPASS_MEETING_GATE=1`.

## Workflow Sync Hook (Cartographer Artifact Hook)

Workflow state is maintained by two complementary mechanisms:

**1. `scripts/workflow_hooks.py`** — fires on every Agent spawn (PreToolUse + PostToolUse) only. Records each spawn as an in-flight row in the `## In-Flight Tasks` table and appends to the `## Real-Time Event Log`. Pre-spawn sets status `spawned`; post-spawn marks it `acknowledged`. Silent no-op outside a research project.

- **Hook**: PreToolUse + PostToolUse on `Agent` → `scripts/workflow_hooks.py`

**2. `/sync-workflow` (on-demand)** — run `python scripts/sync_workflow.py --project <project-dir>` after gate steps, stage completion, or when `lineage:` front-matter is added to an artifact file. Performs a deterministic filesystem walk, reads YAML front-matter from artifact files, rebuilds `workflow_map.live.json`, and updates the Gate Status table in `docs/process/live_workflow_diagram.md`.

Lineage nodes and edges are declared in the artifact file itself using `lineage:` YAML front-matter. The script discovers lineage-bearing artifacts at these paths:

| Path glob | Auto-derived fields |
|---|---|
| `docs/model_versions/<id>.md`     | `lineage_kind=model_version`, `model_version=<id>` |
| `literature/reviews/<paper_id>.md`| `lineage_kind=paper`, `paper_id=<paper_id>` |
| `docs/claims/<claim_id>.md`       | `lineage_kind=claim`, `requires_researcher_review=true` |
| `outputs/figures/*.png|pdf|svg|jpg` | `lineage_kind=figure`, `thumbnail_path=<rel>` |
| `errors/*.err`                    | `lineage_kind=anomaly`, `status=blocked` |

Cross-referential edges (`evolved_from`, `reproduces`, `cites_paper`, `supports`, `limits`) are added via `lineage:` front-matter in the relevant artifact file. See `skills/sync-workflow/SKILL.md` for the full front-matter spec.

## Lineage Coverage Gate

`scripts/check_lineage_coverage.py` surfaces silent failures where a skill's Lineage Front-Matter block was skipped and a node was seeded without its required edges. Advisory by default; the Stage Checkpoint embeds the report and `--strict` exits 2 on any violation.

- **Script**: `python scripts/check_lineage_coverage.py --project <project-dir> [--strict] [--json]`
- **Rules**:
  - `claim` node must carry ≥1 outgoing `supports` or `contradicts` edge.
  - `model_version` whose id is not `model_v1` (and isn't flagged `first_model_version: true`) must carry an outgoing `evolved_from` edge.
  - `paper` node must have ≥1 incoming `cites_paper` or `reproduces` edge (orphan paper review otherwise).
  - Unresolved `anomaly` node must carry ≥1 outgoing `limits` edge to the threatened downstream node.
- **Stage Checkpoint integration**: `scripts/write_stage_checkpoint.py` calls `detect_lineage_coverage()` and renders the violation table under the new `## Lineage Coverage` section — the next stage's agent sees missing edges before loading any results.

## Broken-Edge Linter

`scripts/sync_workflow.py --validate-edges` scans the project-local `workflow_map.live.json` for `graph_links.from`/`graph_links.to` and `edges` references that point at node ids not present in the same map. Catches typos that the Cytoscape renderer otherwise silently drops.

- **Script**: `python scripts/sync_workflow.py --project <project-dir> --validate-edges`
- **Decision**: exits 2 with a list of dangling endpoints; exits 0 with a clean report when every reference resolves.

## Capability Manifest Hook

`scripts/check_harness_manifest.py` validates the deterministic contract in `docs/harness/capability_manifest.json`. It keeps prose, checkers, workflow gate keys, and wired local hooks from drifting apart.

- **Script**: `python scripts/check_harness_manifest.py --project <project-dir>`
- **Decision**: exits 1 when a capability references a missing script/doc, `workflow_gate_keys` do not match the real keys in `scripts/generate_workflow_map.py`, a hook command does not use `$CLAUDE_PROJECT_DIR`, or a wired hook is absent from both `hook_registry` and `known_uncovered_wired_hooks`.
- **Registry docs**: see `docs/harness/hook_registry.md` for the readable summary; the machine source of truth is `docs/harness/capability_manifest.json`.

## Re-spawn Monitoring (not a hook — surfaces in stage checkpoint)

`scripts/write_stage_checkpoint.py` reports re-spawn hotspots (files with ≥ 3 Implementation Agent entries in `docs/gates/agent_spawn_log.md`) alongside the cross-tier verdict. Re-spawns are normal (the Graduate Student code review can reject a draft and re-spawn the Implementation Agent), but a hotspot signals a poor spec, an ambiguous task, or a buggy Implementation Agent pass that the researcher should inspect at the stage gate.

## Hook Registration

Hook registrations live in `.claude/settings.local.json`. Current shape:

| Phase | Matcher | Script |
|---|---|---|
| PreToolUse | `Agent` | `enforce_gate_sequence.py`, `workflow_hooks.py pre`, `check_peer_review_invocation.py` |
| PreToolUse | `Write\|Edit` | `check_src_write_authorization.py`, `path_check_hooks.py pre`, `workflow_hooks.py pre` |
| PreToolUse | `Bash\|PowerShell` | `check_bash_code_write.py`, `check_seed_before_full_run.py`, `warn_orphan_checkpoints.py` |
| PostToolUse | `Agent` | `workflow_hooks.py post`, `check_spawn_log_integrity.py` |
| PostToolUse | `Write\|Edit` | `workflow_hooks.py post`, `path_check_hooks.py post` |
| PostToolUse | `Bash\|PowerShell` | `workflow_hooks.py post`, `path_check_hooks.py post` |

Hook commands should use `python "$CLAUDE_PROJECT_DIR/scripts/<script>.py"` so installed projects run the hook from the project root regardless of the shell's current working directory.

Adding a new hook: write the script, append it to the appropriate matcher block in `settings.local.json`, register it in `docs/harness/capability_manifest.json`, run `python scripts/check_harness_manifest.py --project <project-dir>`, and add a short bullet to `AGENTS.md` linking back to this reference file.
