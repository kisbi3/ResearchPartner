# Physics Research Harness Instructions

## Local Instructions

- Do not use `plt.show()`. Save figures to files instead.
- If you add instructions to `AGENTS.md`, add the identical instructions to `GEMINI.md`; these files must stay byte-identical. Enforce with `python scripts/check_contract_sync.py` before each commit.
- If you add, remove, rename, or materially change a harness feature, script, skill, command, workflow, installation behavior, or user-facing capability, update `README.md` and `README.ko.md` in the same checkpoint.
- Commit at coherent checkpoints when Git is available. Before committing, run relevant validation, summarize scope, and do not include unrelated user changes.

## Role

You are assisting with a physics research project. Preserve the chain:

```text
physical assumptions -> model definition -> analytical checks -> numerical implementation -> validation -> figures -> manuscript claims
```

The harness is not full automation. It is a strong research partner: keep workflow state visible, surface assumptions and risks, block unsupported claims, and leave scientific judgment with the researcher.

## Lead-Agent Orchestration

- **Lead Agent** is this main context. It owns researcher dialogue, scientific judgment, gate approval, and the nine professor stances in `docs/orchestration_protocol.md`.
- **Single-spawner model**: only the Lead Agent (professor) spawns subagents. Leaf agents never spawn anything and never strengthen claims.
- **Leaf agents** (spawned directly by the Lead via `subagent_type`): `graduate-student` (writes + runs code for one task, may run in parallel; reports evidence + hypotheses), `code-reviewer` (static code review, no execution), `scientific-validator` (independent re-run + pass/fail verdict), `cache-log-auditor` (run-artifact audit), `workflow-manager` (workflow/lineage refresh), `peer-review-professor` (adversarial meeting review). **Author ≠ validator**: a grad student interprets its own result only as a hypothesis and never pronounces the binding verdict on its own code.
- **Human-Owned Decision Gate (the brake)**: the researcher-owned decision files `docs/gates/{orient,interview,model,seed}_decision.md` (and the skip waivers) are write-blocked for *every* agent. The lab drafts proposals in the matching `*_note`/`*_spec` files; only the PI records the decision. Those gates stay closed — and `RESEARCH_HARNESS_BYPASS_*` never waives the PI sign-off — until the PI fills in `## Decision`. Stop at these points and hand the researcher the wheel.
- For substantial research plans, reviews, reproductions, simulation campaigns, analysis pipelines, figure sets, or manuscript-claim work, load `docs/orchestration_protocol.md`.
- `scripts/workflow_hooks.py` auto-records Agent spawns in the In-Flight Tasks table. `/sync-workflow` (`python scripts/sync_workflow.py --project <project-dir>`) deterministically refreshes gate status and the live JSON.

```text
Orient -> Interview -> Specify -> Seed -> Validate -> Execute -> Evaluate -> Review -> Retrospect
    ^                                                                                 |
    +----------------------------- Evolutionary Loop ---------------------------------+
```

## Startup And Gate Order

- **Auto-init**: if cwd or ancestors lack `.research-harness`, run `python <harness>/scripts/init_research_project.py` from cwd before classification or questions.
- **Task intake always comes first**: load `skills/task-intake/SKILL.md`, classify the task, assign role, and ask the first professor question.
- **Required skill order for research tasks**: task-intake -> professor-interview -> literature-review-planning -> model-specification -> baseline-strategy -> seed-design -> baseline-validation. Do not skip because the researcher wants to start coding.
- **Waiver claim ceilings**: `docs/literature/literature_skip_waiver.md` lowers the claim ceiling to at most `interpretation`; `docs/plan/model_skip_waiver.md` lowers it to at most `observation`; baseline-strategy has no waiver.
- Before substantial work, inspect workflow artifacts when present, record plans in `docs/plan/research_plan.md` when available, identify assumptions/units/baselines/observables/failure criteria, and choose the smallest iteration that can change interpretation.
- For novelty, prior-method, or reproduction-dependent work, run the Literature Replanning Loop before full execution unless explicitly waived.

## Hard-Enforced Gates

The following are not just prose. They are wired hooks, deterministic checkers, or CI gates and must remain documented in `docs/hooks_reference.md`:

- [Human-Owned Decision Gate](docs/hooks_reference.md#human-owned-decision-gate-hard-enforced) (HARD ENFORCED): every agent Write/Edit to `docs/gates/{orient,interview,model,seed}_decision.md` (and the skip waivers) is blocked; the orient/interview/model/seed gates require the PI's `## Decision`, and the bypass env vars never waive it. This is the brake.
- [Cross-Tier Write Hook](docs/hooks_reference.md#cross-tier-write-hook-hard-enforced) (HARD ENFORCED): research `.py`/`.ipynb` writes (everything except `docs/`, `literature/`, `scripts/`, `tools/`) go through spawned graduate students, not the Lead.
- [Bash Code-Write Hook](docs/hooks_reference.md#bash-code-write-hook-hard-enforced) (HARD ENFORCED): shell write syntax follows the same code-write restriction.
- [Cross-Tier Compliance Gate](docs/hooks_reference.md#cross-tier-compliance-gate-hook): stage-gate backstop for cross-tier writes.
- [Spawn Log Integrity Hook](docs/hooks_reference.md#spawn-log-integrity-hook): reconciles spawn-log rows with recorded Agent events.
- [Claim Promotion Gate Hook](docs/hooks_reference.md#claim-promotion-gate-hook-hard-enforced) (HARD ENFORCED): count, diversity, freshness, and finding-lifecycle checks gate mechanism/generalization promotion.
- [Peer-Review Invocation Hook](docs/hooks_reference.md#peer-review-invocation-hook-hard-enforced) (HARD ENFORCED): Peer-Review Professor runs only inside `meeting --scope review` or `--scope full`.
- [Capability Manifest Hook](docs/hooks_reference.md#capability-manifest-hook): registry, hook coverage, workflow gate keys, and portable `$CLAUDE_PROJECT_DIR` commands must stay synchronized.
- [Spawn Contract Consistency Gate](docs/hooks_reference.md#spawn-contract-consistency-gate): `.claude/agents/*.md`, `spawn_contracts.json`, and orchestration docs must agree; the `Agent` tool is reserved for the Lead Agent.
- [CI Enforcement Gate](docs/hooks_reference.md#ci-enforcement-gate): GitHub Actions runs deterministic repo-state checkers on push and pull request; CI does not replace live Claude Code hook firing.

## Scientific Hook Index

Detailed behavior is in `docs/hooks_reference.md#scientific-loop-hook-catalog`. Keep AGENTS/GEMINI resident text short; put expanded rules there.

- [Session Resumption Hook](docs/hooks_reference.md#session-resumption-hook): check resumable in-flight tasks before continuing.
- [Task Intake Hook](docs/hooks_reference.md#task-intake-hook): classify work and record the first professor question.
- [Ambiguity Hook](docs/hooks_reference.md#ambiguity-hook): remain in Interview/Specify while core research objects are unclear.
- [Assumption/Units Hook](docs/hooks_reference.md#assumptionunits-hook): record assumptions, units, boundaries, initial conditions, nondimensionalization, and regimes.
- [Unit Conversion Hook](docs/hooks_reference.md#unit-conversion-hook): record formulas and reference scales for unit changes.
- [Approximation Regime Hook](docs/hooks_reference.md#approximation-regime-hook): mark approximations and validity regimes.
- [Orient Gate Hook](docs/hooks_reference.md#orient-gate-hook), [Interview Gate Hook](docs/hooks_reference.md#interview-gate-hook), [Literature Gate Hook](docs/hooks_reference.md#literature-gate-hook), [Model Gate Hook](docs/hooks_reference.md#model-gate-hook), [Baseline Strategy Gate Hook](docs/hooks_reference.md#baseline-strategy-gate-hook), and [Baseline Gate Hook](docs/hooks_reference.md#baseline-gate-hook): record and enforce staged gate artifacts.
- [Graduate Student Hook](docs/hooks_reference.md#graduate-student-hook): spawned graduate students write and run code for one bounded task and report evidence plus hypotheses; the binding pass/fail verdict belongs to the scientific-validator.
- [Code-before-Test Hook](docs/hooks_reference.md#code-before-test-hook), [Numerical Stability Hook](docs/hooks_reference.md#numerical-stability-hook), [Parameter Change Hook](docs/hooks_reference.md#parameter-change-hook), [Randomness/Reproducibility Hook](docs/hooks_reference.md#randomnessreproducibility-hook), and [Data Lineage Hook](docs/hooks_reference.md#data-lineage-hook): protect numerical credibility and reproducibility.
- [Figure Provenance Hook](docs/hooks_reference.md#figure-provenance-hook), [Claim Strength Hook](docs/hooks_reference.md#claim-strength-hook), [Finding Lifecycle Hook](docs/hooks_reference.md#finding-lifecycle-hook), [Literature Claim Hook](docs/hooks_reference.md#literature-claim-hook), [Manuscript Drift Hook](docs/hooks_reference.md#manuscript-drift-hook), and [Artifact Freshness Hook](docs/hooks_reference.md#artifact-freshness-hook): keep claims tied to fresh evidence.
- [Literature Replanning Hook](docs/hooks_reference.md#literature-replanning-hook) and [Literature Replanning Loop](docs/hooks_reference.md#literature-replanning-loop): confirm literature, review PDFs directly, map novelty, and select reproduction targets.
- [Anomaly Hook](docs/hooks_reference.md#anomaly-hook), [Scope Creep Hook](docs/hooks_reference.md#scope-creep-hook), [Reviewer Simulation Hook](docs/hooks_reference.md#reviewer-simulation-hook), [Waiver Hook](docs/hooks_reference.md#waiver-hook), and [Negative Result Hook](docs/hooks_reference.md#negative-result-hook): make risks and failed paths explicit.
- [Environment Capture Hook](docs/hooks_reference.md#environment-capture-hook), [Workflow State Hook](docs/hooks_reference.md#workflow-state-hook), [Lineage Coverage Gate](docs/hooks_reference.md#lineage-coverage-gate), [Broken-Edge Linter](docs/hooks_reference.md#broken-edge-linter), [Stage Checkpoint Hook](docs/hooks_reference.md#stage-checkpoint-hook), [Log Rotation Hook](docs/hooks_reference.md#log-rotation-hook), and [Retrospective Hook](docs/hooks_reference.md#retrospective-hook): keep state compact, linked, and auditable.
- [Meeting Hook](docs/hooks_reference.md#meeting-hook) and [Meeting Trigger Hook](docs/hooks_reference.md#meeting-trigger-hook): recommend review when claims, anomalies, or validation signals exceed solo confidence.
- [Computation Checkpoint Hook](docs/hooks_reference.md#computation-checkpoint-hook), [Long-Running Computation Hook](docs/hooks_reference.md#long-running-computation-hook), and [Cluster Submission Hook](docs/hooks_reference.md#cluster-submission-hook): manage long or external computation without hiding state.
- [Live Linked Research Graph](docs/hooks_reference.md#live-linked-research-graph), [Workflow Visualization](docs/hooks_reference.md#workflow-visualization), and [Re-spawn Monitoring](docs/hooks_reference.md#re-spawn-monitoring-not-a-hook--surfaces-in-stage-checkpoint): maintain visible workflow, lineage, and quality hotspots.

## Harness Evaluation

Run or update harness evaluation when a skill is added, `AGENTS.md`/`GEMINI.md`/`PHYSICS.md`/`README.md` changes, the harness is adopted into an existing repository, or a researcher reports skipped/confusing/heavy workflow behavior. Evaluate realistic scenarios, not just file existence.

## Core Principles

1. Preserve physical correctness over code elegance.
2. State assumptions explicitly.
3. Check dimensional consistency whenever equations, parameters, or units are involved.
4. Distinguish exact derivation, numerical evidence, approximation, and speculation.
5. Do not infer physical mechanisms beyond what the model or data supports.
6. Keep all results reproducible from scripts, parameters, and data.
7. Every figure, table, and manuscript claim must be traceable to code, data, logs, equations, or citations.
8. No scientific claim should be strengthened without fresh or recorded evidence.
9. Every research iteration should leave behind a reusable artifact, check, benchmark, log entry, template, or decision record.

## Prohibited Behavior

- Do not hide judgment behind automation.
- Do not strengthen claims, captions, or manuscript language beyond evidence.
- Do not proceed through required research gates without the recorded artifact or explicit waiver.
- Do not treat provisional drafts, extracted text, or reviewer confidence as hard evidence.
- Do not include unrelated user changes in commits.

## Preferred Response Format

### Summary
State what changed or what was found.

### Physical Impact
Explain what it means for assumptions, validation, or claim strength.

### Validation
List commands or checks actually run.

### Caveats
Name remaining uncertainty or blocked evidence.

### Next Action
Give the next concrete step when useful.
