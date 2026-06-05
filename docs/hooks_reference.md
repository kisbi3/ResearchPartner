# Hooks Reference

Detailed descriptions of the harness's automated enforcement hooks. `AGENTS.md` / `GEMINI.md` link to this file rather than inlining the descriptions so the contract files stay compact (every spawned subagent that loads `AGENTS.md` pays for that prose). Soft "discipline" hooks (Numerical Stability, Anomaly, Scope Creep, etc.) stay inline in `AGENTS.md`; the entries here are the ones that involve a script, a hook registration, or an enforcement decision.

**Label vocabulary.** *HARD ENFORCED* = wired as a blocking PreToolUse/PostToolUse hook that fires at tool-call time (some carry an explicit `RESEARCH_HARNESS_BYPASS_*` escape hatch). *Unbypassable* = additionally has no env-var escape — only the Human-Owned Decision Gate qualifies. An entry with a `**Script:**`/`**Invocation:**` line and no `**Hook:**` line is a CLI/CI checker the Lead Agent or CI runs deliberately; it is **not** a write-time block. Where a section mixes both (e.g. Claim Promotion Gate), the per-bullet label says which layer is wired.

## Human-Owned Decision Gate (HARD ENFORCED)

The brake. The harness's #1 principle — leave scientific judgment with the researcher — made enforceable. The researcher-owned decision files are write-blocked for *every* agent (Lead/professor included), so the lab can propose but never sign its own approval or its own bypass.

- **Files (PI-only)**: `docs/gates/{orient,interview,model,seed,adoption}_decision.md`, `docs/plan/model_skip_waiver.md`, `docs/literature/literature_skip_waiver.md`.
- **Write-block**: PreToolUse on `Write|Edit` → `scripts/path_check_hooks.py` exits 2 on any agent write to those paths. The lab drafts proposals in the matching `*_note`/`*_spec` files; the PI records the decision directly (outside the agent's tools).
- **Gate requirement**: `check_orient_recorded.py`, `check_interview_recorded.py`, and `check_model_specified.py` require a non-empty `## Decision`; `check_seed_before_full_run.py` requires `docs/gates/seed_decision.md` before any heavy run; `enforce_gate_sequence.py` keeps a `HUMAN_GATES = {orient, interview, model}` set.
- **Adoption decision (brownfield onboarding)**: `docs/gates/adoption_decision.md` is the PI-only brake for attaching the harness to research already in progress. The harness gate chain is greenfield-shaped (it expects a fresh model spec + baseline strategy), but an existing project already has both. When the PI signs this file, `check_adoption_recorded.py` reports **adoption mode** active, and `enforce_gate_sequence.py` treats the Model and Baseline-strategy gates as **satisfied-by-adoption** (the existing model and chosen reproduction baseline are accepted by the signed decision — not re-authored from scratch). The Baseline gate and the orient/interview human gates are unchanged: a claim is validated only after the chosen result is actually reproduced and recorded in `baseline_registry.md`. On a fresh greenfield project the file stays a blank stub and adoption mode is inactive.
- **Unbypassable**: `RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE` / `RESEARCH_HARNESS_BYPASS_SEED_GATE` waive only the quality/sequence and smoke-run gates — never the PI's decision. (Agents cannot set those env vars anyway: an inline `VAR=1 cmd` does not reach the PreToolUse hook process.)

## Cross-Tier Write Hook (HARD ENFORCED)

Every `.py` or `.ipynb` file written anywhere under the project root (marked by `.research-harness`; layout v3 has no `ResearchPartner-runs/<run>/` wrapper) must come from a spawned graduate-student — except files under `docs/`, `literature/`, `scripts/`, and `tools/` (notes, PDFs, and vendored harness tooling; `tests/` is research code and IS covered). The Lead Agent (professor) does not write research code; it spawns graduate students who do.

- **Hook**: PreToolUse on `Write|Edit` → `scripts/check_src_write_authorization.py`
- **Decision**: allow iff `docs/gates/agent_spawn_log.md` has a matching `graduate-student` row for the target file, or was modified within the last 10 minutes.
- **Bypass**: `RESEARCH_HARNESS_BYPASS_SRC_GATE=1` for an explicit one-off waiver.

## Bash Code-Write Hook (HARD ENFORCED)

Closes the Bash bypass of the cross-tier write hook. Bash commands such as `echo … > sim.py`, `cat <<EOF > sim.py`, `sed -i … sim.py`, `cp other.py <run>/src/sim.py`, `python -c "open('sim.py', 'w')…"`, `Set-Content`, or `Out-File` would otherwise produce code without triggering Write/Edit.

- **Hook**: PreToolUse on `Bash|PowerShell` → `scripts/check_bash_code_write.py`
- **Decision**: block any command whose shell-write syntax (`>`, `>>`, `tee`, `sed -i`, `cp/mv/install/rsync`, heredoc redirect, `Set-Content`/`Out-File`/`Add-Content`, `python -c "open(…,'w')"`) targets a `.py`/`.ipynb` path inside the project, outside the exempt top-level dirs (`docs/`, `literature/`, `scripts/`, `tools/`).
- **Bypass**: same `RESEARCH_HARNESS_BYPASS_SRC_GATE=1`.

## Cross-Tier Compliance Gate Hook

Backstop for the two write hooks above. Run before advancing a stage gate.

- **Script**: `python scripts/check_cross_tier_compliance.py --project <project-dir> [--strict]`
- **Decision**: exits 2 when `src/*.py` files exist without matching graduate-student spawn records. `--strict` also fails on missing spawn log.

## Spawn Log Integrity Hook

`docs/gates/agent_spawn_log.md` is plain Markdown — a forged row could let a direct code write pass the cross-tier hook. This script reconciles spawn-log rows against Agent() start events recorded automatically by `workflow_hooks.py` in `<run>/docs/live_workflow_diagram.md`.

- **Script**: `python scripts/check_spawn_log_integrity.py --project <project-dir>`
- **Decision**: exits 2 when, for any date bucket, the spawn log has more `graduate-student` rows than the diagram has Agent() `start` events whose description mentions "graduate".

## Claim Promotion Gate Hook

Run before the Lead Agent promotes the run's claim ceiling above `observation`.

**Enforcement — two layers, only one is wired:**

- **Freshness + finding-lifecycle structure — HARD ENFORCED (wired).** PreToolUse on `Write|Edit` to `docs/claims/*.md` → `scripts/path_check_hooks.py` invokes `scripts/check_claim_promotion_freshness.py`, which blocks (exit 2) a promoted claim whose cited `outputs/` artifacts are stale/missing, or whose mechanism/generalization finding lifecycle is incomplete.
- **Count + diversity — NOT a live hook.** `scripts/check_claim_promotion.py` is a CLI checker the Lead Agent runs before promoting, and CI runs on a fixture (via `evaluate_harness.py`). It is enforced by Lead discipline + CI, *not* by a write-time block — nothing at write time stops a promoted claim that skipped it.

Checker detail (`check_claim_promotion.py`, the non-wired count/diversity layer):

- **Invocation**: `python scripts/check_claim_promotion.py --run <run-dir> --target <observation|interpretation|mechanism|generalization>`
- **Input**: `docs/gates/validation_log.md` rows (`| Date | Check | Target | Status | Evidence |`).
- **Count gate**: interpretation ≥ 1 pass; mechanism ≥ 2 pass; generalization ≥ 3 pass.
- **Diversity gate**: `mechanism` requires ≥ 1 baseline-class pass (Check matching `toy_model | reproduction | analytical | conservation | dimensional | known_limit`). `generalization` requires ≥ 2 distinct Check categories.
- **Finding Lifecycle Hook**: for `mechanism` and `generalization`, the affected `docs/claims/<claim_id>.md` must include a `## Finding Lifecycle` section. Candidate findings cannot promote; `independently_checked` and `evidence_linked` must be declared; `false_alarm` cannot promote; and `## Evidence Paths Read Directly` must contain at least one existing project path.
- **Direct-read boundary**: the checker validates only declared structure and path existence. It cannot prove the Lead actually read a file.
- **Bypass**: lower the target ceiling or add a waivered validation row.

## Peer-Review Invocation Hook (HARD ENFORCED)

A Peer-Review Professor may only be spawned from within a `meeting --scope review` (or `--scope full`) session.

- **Hook**: PreToolUse on `Agent` → `scripts/check_peer_review_invocation.py`
- **Decision**: block when the spawn prompt names the Peer-Review role unless either (a) the same prompt references the `meeting` skill with `--scope review`/`--scope full`, or (b) a `docs/meetings/*.md` artifact under the project root (layout v3 — marked by `.research-harness`, no `ResearchPartner-runs/<run>/` wrapper) was touched within the last 10 minutes.
- **Bypass**: `RESEARCH_HARNESS_BYPASS_MEETING_GATE=1`.

## Workflow Sync Hook

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

## Spawn Contract Consistency Gate

`scripts/check_spawn_contracts.py` validates `docs/harness/spawn_contracts.json` against `.claude/agents/<role>.md`, role skills, and `docs/orchestration_protocol.md`. It is an offline/CI consistency gate for the single-spawner model: the Lead Agent is the only spawner, and all spawned role agents are leaf agents. The script does not itself block a live tool call, but it catches drift before a PR or checkpoint claims the spawn contract is coherent.

- **Script**: `python scripts/check_spawn_contracts.py --project <project-dir>`
- **Decision**: exits 1 when a required leaf role (graduate-student, code-reviewer, scientific-validator, cache-log-auditor, workflow-manager, peer-review-professor) is missing or an unknown role appears, an agent file's frontmatter `name` differs from the `subagent_type`, `tools:` differs from the JSON contract, any role agent includes the `Agent` tool, any role declares child spawns, the description is not explicit-spawn-only, or `docs/orchestration_protocol.md` omits a required leaf `subagent_type`.
- **Layering**: Claude Code's agent loader applies `.claude/agents/<role>.md` `tools:` at runtime; existing path and Bash hooks (`check_src_write_authorization.py`, `check_bash_code_write.py`) still provide hard protection against unauthorized code writes.

## CI Enforcement Gate

`.github/workflows/harness-checks.yml` runs deterministic repo-state checker commands on `push` and `pull_request` across `ubuntu-latest` and `windows-latest`. CI does not replace live Claude Code hook firing — the hooks still fire in the live runtime; CI only catches repo-state drift.

- **Workflow**: `.github/workflows/harness-checks.yml`
- **Commands**: `python -m pytest tests -q`; `python scripts/check_harness_manifest.py`; `python scripts/check_spawn_contracts.py`; `python scripts/check_contract_sync.py`; `python scripts/evaluate_harness.py --fail-on-partial`.
- **Decision**: any command exit code fails CI. `evaluate_harness.py --fail-on-partial` makes new partial scenario coverage a CI failure.
- **Layering**: CI complements `--upgrade-hooks` and local hook installation by enforcing repository-state drift. It cannot prove live Claude Code PreToolUse/PostToolUse hook firing.

## Scientific Loop Hook Catalog

This catalog holds the detailed hook prose that used to live in resident `AGENTS.md`/`GEMINI.md`. Those files keep short routing rules and link here; evaluators include this file in `harness_rule_text()` so moving details here does not weaken scenario coverage.

### Session Resumption Hook

At the start of a continuing session, run `python scripts/check_session_resumable.py --project <project-dir>` and surface `In-Flight Tasks`, blocked or `in_progress` gates, `spawned` rows, and whether each task should continue, retry, be acknowledged, or be abandoned. Abandoned rows are marked `abandoned` in `docs/process/live_workflow_diagram.md`, then `/sync-workflow` refreshes state.

### Task Intake Hook

Load `skills/task-intake/SKILL.md` at the start of every task. It records the `Orient phase`, task classification, responsible role, first professor question, and assigns research roles before execution.

### Ambiguity Hook

If the research question, physical object, observable, failure criterion, or review checkpoint is unclear, remain in Interview/Specify instead of executing.

### Assumption/Units Hook

Record assumptions, units, boundary conditions, initial conditions, nondimensionalization, and approximation regime before relying on equations, parameters, or results.

### Unit Conversion Hook

When SI, cgs, natural units, code units, or nondimensional units are converted, record the conversion formula and reference scale.

### Approximation Regime Hook

Mark linearization, perturbation, continuum, weak-coupling, low/high-temperature, small-angle, or similar approximations with their validity regime.

### Orient Gate Hook

Write task-intake output to `<project>/docs/gates/orient_note.md` with `## Task Classification`, `## Responsible Role`, `## First Professor Question`, and `## Researcher Answer`. Enforce before Seed, Execute, or Evaluate with `python scripts/check_orient_recorded.py --project <project-dir>`.

### Interview Gate Hook

Write the professor-interview result to `docs/gates/interview_notes.md`, including the crystallized research question, surfaced assumptions, agreed direction, and suggested next skill. Enforce with `check_interview_recorded.py` before Seed or Execute work begins.

### Literature Gate Hook

Write Literature Gate Status (`ready` or `waived`) to `docs/literature/literature_review_plan.md`; enforce with `check_literature_reviewed.py`. A `docs/literature/literature_skip_waiver.md` waiver lowers the claim ceiling to at most `interpretation`.

### Model Gate Hook

Write the model definition to `docs/plan/model_spec.md`; enforce with `check_model_specified.py`. A `docs/plan/model_skip_waiver.md` waiver lowers the claim ceiling to at most `observation`.

### Baseline Strategy Gate Hook

Write `variation` or `new model` plus verification target to `docs/plan/baseline_strategy.md`; enforce with `check_baseline_strategy.py` before Seed. There is no skip waiver. The first seed task is reproduce the parent model for variation or verify against Analytical Checkpoint 1 for new model.

### Baseline Gate Hook

Before a new model, solver, analysis pipeline, or figure workflow is interpreted, require a toy model, known limit, reproduction, conservation check, or explicit waiver. Enforce with `check_baseline_gate.py` before Execute or Evaluate.

### Graduate Student Hook

Use `skills/seed-design/SKILL.md` to break the work into bounded seed tasks (exact files, commands, inputs, outputs, observables, pass/fail criteria, evidence records, failure handling, `Seed phase` boundaries), then spawn a `graduate-student` per task — in parallel where the dependency map allows. A graduate student writes and runs its task's code and reports evidence plus hypotheses; it does not pronounce the binding verdict (the scientific-validator does) or promote claims. See `skills/graduate-student/SKILL.md` and `docs/orchestration_protocol.md`.

### Code-before-Test Hook

For numerical, simulation, analysis, or figure-generation code, flag implementation that lacks a prior or accompanying validation check.

### Numerical Stability Hook

When solvers, timesteps, grids, tolerances, convergence criteria, integration schemes, sampling, or fitting routines are involved, require stability, convergence, uncertainty, or sensitivity checks. Visual agreement alone is not validation.

### Parameter Change Hook

Record parameter values, sweep ranges, timestep, grid size, tolerance, random seed, sample size, and changes from previous runs.

### Randomness/Reproducibility Hook

For stochastic sampling, Monte Carlo, bootstrap, train/test split, randomized initialization, or noise, record seeds and run metadata; seedless results are provisional.

### Data Lineage Hook

Record raw data, processed data, filters, smoothing, clipping, outlier removal, normalization, fits, and derived datasets.

### Figure Provenance Hook

Every figure should trace to script, input data, command, parameters, output path, and caption claim. Enforce after figures with `python scripts/check_figure_provenance.py --project <project-dir>`.

### Claim Strength Hook

When claims, captions, conclusions, README text, or manuscript text change, check wording strength against the weakest evidence and downgrade unsupported language. No scientific claim should be stronger than its evidence path.

### Finding Lifecycle Hook

Mechanism and generalization promotion must reject candidate findings. A finding can promote only after independent checking, `Evidence Paths Read Directly`, evidence-linked state, and no `false_alarm` state. The checker validates only declared structure; it cannot prove the Lead Agent actually read the file. The peer-review confidence threshold is reviewer surface guidance, not a hard checker.

### Literature Claim Hook

Novelty, priority, "to our knowledge", "first", "known result", and prior-work claims require citations or must be marked unverified.

### Literature Replanning Hook

Run the Literature Replanning Loop when novelty, prior methods, reproduction fidelity, or a literature claim could change the plan. The Lead Agent first confirms citation identity by web discovery, requests researcher-provided PDFs only when access fails, stores them under `literature/pdfs/`, writes a novelty map, chooses reproduction targets, and replans before full-scale work.

### Literature Replanning Loop

The loop builds section-by-section paper review notes, includes a `Figure/Table-by-Figure/Table Review`, and follows this rule: PDF text extraction is a reading aid, not evidence by itself. It may use `process_paper_for_review.py`, keeps clickable links across the literature graph, runs `check_paper_review_quality.py`, and may add a `Machine-Assisted Draft From Extracted Text` section that remains provisional until direct PDF review.

### Manuscript Drift Hook

Detect when manuscript language becomes stronger than the current evidence chain or diverges from recorded assumptions and limitations.

### Artifact Freshness Hook

After code, data, parameters, or analysis change, mark dependent figures, tables, captions, and manuscript references stale until regenerated or revalidated.

### Anomaly Hook

Surprising, unstable, contradictory, or failed results must be classified against expected behavior before patching symptoms.

### Scope Creep Hook

New observables, claims, parameter sweeps, figures, or goals that appear mid-run must be accepted into the seed explicitly or deferred.

### Reviewer Simulation Hook

Before major claims or figures are treated as ready, generate skeptical reviewer questions and check whether the evidence answers them.

### Waiver Hook

If the researcher bypasses a baseline, unit, reproduction, stability, or evidence gate, record the waiver, reason, risk, and claim limits.

### Negative Result Hook

Failed baselines, null results, disappearing effects, and invalidated hypotheses should be recorded rather than silently discarded.

### Environment Capture Hook

For important runs, record command, OS, Python/package versions, relevant environment, and git state when available.

### Workflow State Hook

workflow_hooks.py (hook-driven, not spawned) listens to the Lead Agent and leaf Coding Subagents, records process state in the live workflow artifact, tracks active step, gates, and evidence links, must not strengthen scientific claims, and does not give project opinions. `/sync-workflow` is the on-demand deterministic refresh path.

### Coding Subagent Claim Discipline

Leaf Coding Subagents do bounded implementation, validation, audit, or figure work. They should not decide that evidence supports a stronger scientific claim; the Lead Agent performs that judgment from recorded artifacts.

### Completion Conference Reporting

At major completion points, the Lead Agent performs a completion conference across all leaf-agent reports (graduate-student evidence + hypotheses, code-review/validator/auditor verdicts) and the latest workflow state, gathers visualization materials and validation evidence, then reports to the PI with claim limits and caveats.

### Retrospective Hook

Every research iteration should leave a reusable artifact, check, benchmark, log entry, template, decision record, outcome, failure, negative result, open question, or lineage entry.

### Workflow State Hook

After completing a gate step, finishing a stage, or changing evidence links, run `/sync-workflow` (`python scripts/sync_workflow.py --project <project-dir>`) so the live workflow state remains current.

### Stage Checkpoint Hook

At the end of every research stage, write `docs/checkpoints/stage_N_checkpoint.md` with `python scripts/write_stage_checkpoint.py --project <project-dir> --stage N`; later agents load the compact checkpoint instead of raw logs unless a specific value needs deeper inspection.

### Log Rotation Hook

When Markdown-table logs exceed roughly 50 entries or during stage checkpointing, run `python scripts/rotate_log.py --log <path>` to archive closed rows while keeping active rows and rules live.

### Meeting Hook

When the Lead Agent cannot answer reliably alone, convene `meeting --scope quick`, `meeting --scope review`, or `meeting --scope full`; record outcomes in `docs/meetings/YYYY-MM-DD-<slug>.md` and run `/sync-workflow` when lineage changes.

### Meeting Trigger Hook

Recommend a meeting for failed or partial baseline validation, uncertain anomaly causes, mechanism/universality/novelty claims, contradictory numerical validation signals, or contested baseline strategy decisions.

### Computation Checkpoint Hook

For any `src/` script with a long-running loop, use `CheckpointManager` from `scripts/run_with_checkpoint.py`, checkpoint under `cache/checkpoint_<stem>.pkl`, and run `check_computation_resumable.py` to find orphaned checkpoints.

### Long-Running Computation Hook

When a simulation, solver, analysis pipeline, or parameter sweep will take more than roughly two minutes, use background execution and monitor outputs instead of filling the conversation with polling; record command, expected outputs, and duration in docs.

### Cluster Submission Hook

Claude runs locally and cannot submit HPC jobs directly. Detect or ask for scheduler details, write the batch script, tell the researcher the submission command and files to retrieve, then wait for returned stdout, stderr, and results before analysis.

### Live Linked Research Graph

`workflow_map.html` and `workflow_map.live.json` maintain Code links, Result links, Interpretation links, Link Status, Evidence Strength, Claim ceiling, Researcher Checkpoint Marker, Artifact Preview, and Staleness propagation. Use `skills/sync-workflow/SKILL.md`, `lineage:` front-matter, graph links, and `/sync-workflow` to keep it current.

### Workflow Visualization

Before substantial work, inspect `Workflow Visualization`, `workflow_map.html`, `paper_logic_diagram`, `docs/process/live_workflow_diagram.md`, and `sync_workflow.py` output when present.

## Re-spawn Monitoring (not a hook — surfaces in stage checkpoint)

`scripts/write_stage_checkpoint.py` reports re-spawn hotspots (files with ≥ 3 graduate-student entries in `docs/gates/agent_spawn_log.md`) alongside the cross-tier verdict. Re-spawns are normal (the Code Reviewer can reject a draft and the professor re-spawns the graduate student), but a hotspot signals a poor spec, an ambiguous task, or buggy graduate-student output that the researcher should inspect at the stage gate.

## Hook Registration

Hook registrations live in `.claude/settings.local.json`. Current shape:

| Phase | Matcher | Script |
|---|---|---|
| PreToolUse | `Agent` | `enforce_gate_sequence.py`, `workflow_hooks.py pre`, `check_peer_review_invocation.py` |
| PreToolUse | `Write\|Edit` | `check_src_write_authorization.py`, `path_check_hooks.py pre` |
| PreToolUse | `Bash\|PowerShell` | `check_bash_code_write.py`, `check_seed_before_full_run.py`, `warn_orphan_checkpoints.py` |
| PostToolUse | `Agent` | `workflow_hooks.py post`, `check_spawn_log_integrity.py` |
| PostToolUse | `Write\|Edit` | `path_check_hooks.py post` |
| PostToolUse | `Bash\|PowerShell` | `path_check_hooks.py post` |

Hook commands should use `python "$CLAUDE_PROJECT_DIR/scripts/<script>.py"` so installed projects run the hook from the project root regardless of the shell's current working directory.

Adding a new hook: write the script, append it to the appropriate matcher block in `settings.local.json`, register it in `docs/harness/capability_manifest.json`, run `python scripts/check_harness_manifest.py --project <project-dir>`, and add a short bullet to `AGENTS.md` linking back to this reference file.
