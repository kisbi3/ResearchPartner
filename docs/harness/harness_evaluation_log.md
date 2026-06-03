# Harness Evaluation Log

| ID | Date | Scope | Command / Method | Result | Main Gap | Next Evaluation |
|---|---|---|---|---|---|---|
| HE-001 | 2026-05-13 | Core scenario coverage | `python scripts/evaluate_harness.py` | 5 pass, 1 partial, 0 fail, average 98 | Anomaly scenario needed stronger top-level expected behavior wording | Re-run after rule update |
| HE-002 | 2026-05-13 | Core scenario coverage after rule update | `python scripts/evaluate_harness.py` | 6 pass, 0 partial, 0 fail, average 100 | Automated evaluation is static; needs live pilot | Run `docs/harness/harness_pilot_protocol.md` on a real or mock research task |
| HE-003 | 2026-05-13 | Workflow navigation and paper logic coverage | `python scripts/evaluate_harness.py` | 7 pass, 0 partial, 0 fail, average 100 | Still needs live researcher pilot of `docs/workflow_map.html` | Run pilot before first real research campaign |
| HE-004 | 2026-05-13 | Live workflow pilot after 1D diffusion run | `python scripts/evaluate_harness.py`; `python -m pytest tests`; review of `ResearchPartner-runs/2026-05-13-1d-diffusion-mode-decay` artifacts | 8 pass, 0 partial, 0 fail, average 100; 5 tests passed | Strong structurally, but still relies on the agent regenerating `workflow_map.html` after live workflow updates; anomaly path has not been exercised with a real failed run | Run an intentional anomaly pilot and consider automating live workflow regeneration |
| HE-005 | 2026-05-13 | Strong-partner framing and intentional anomaly pilot | `python scripts/evaluate_harness.py`; `python -m pytest tests`; `python -m pytest ResearchPartner-runs/.../tests`; `python scripts/validate_workflow_links.py` | 8 pass, 0 partial, 0 fail, average 100; harness tests passed; run tests passed | Framing now explicitly rejects full automation, and the numerical-instability anomaly path was exercised; remaining gap is researcher review of whether the partner-style stop feels clear enough | Ask researcher to choose fixed-ratio convergence, multi-mode validation, or another anomaly class |
| HE-006 | 2026-05-14 | Docs shallow-structure reorganization | `python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py -q`; `python scripts/evaluate_harness.py`; `python scripts/validate_workflow_links.py`; `python scripts/run_baseline_validation.py` | 7 tests passed; 12 pass, 0 partial, 0 fail, average 100; workflow links passed; baseline harness check passed | Structural paths are updated, but tracked Python cache files can still change during validation | Decide whether generated `__pycache__` files should remain tracked |
| HE-007 | 2026-06-03 | Behavioral re-evaluation + enforcement hardening | hook-firing probes (`path_check_hooks`, `enforce_gate_sequence`, `check_src_write_authorization`); `python -m pytest tests -q`; `python scripts/evaluate_harness.py --fail-on-partial` | 264 tests pass; 30 pass / 0 partial / 0 fail, avg 100; probes confirmed the brake + cross-tier block and exposed a gate-sequence rewording bypass (fixed this cycle) | Self-hosting over-gating of harness dev; `update_harness.py` does not refresh hooks; `evaluate_harness` still presence-based | Re-run after addressing the deferred backlog (see HE-007 detail) or at next adoption |
| HE-008 | 2026-06-03 | Operational hardening follow-up | `python scripts/check_contract_sync.py`; `python scripts/check_harness_manifest.py`; `python scripts/check_spawn_contracts.py`; `python scripts/check_domain_manifest.py`; `python scripts/evaluate_harness.py --fail-on-partial`; `python -m pytest -q`; `git worktree prune --verbose` + worktree audit | contract/manifest/spawn/domain checks passed; structural harness report 30 pass / 0 partial / 0 fail, avg 100; behavioral checker probes 4 run / 4 pass / 0 fail; 271 tests passed; worktree prune had no stale metadata | Registered and unregistered local `.claude/worktrees` directories remain; deletion requires owner review to avoid disrupting other sessions | Re-run after worktree owner review or before publishing the branch |

## HE-007 Detail — 2026-06-03

**Method.** Re-evaluated enforcement by firing the wired hook scripts with crafted JSON payloads (behavioral), not just file/keyword presence. Probes: PI-decision write (expect block), lab-note write (expect allow), `tests/*.py` write (expect block), `docs/*.md` write (expect allow), and graduate-student spawns with vs. without skill keywords (gate detection).

**Scenario coverage.** `evaluate_harness.py` 30/30 (presence). Behavioral probes confirmed: Human-Owned Decision Gate blocks (the brake); Cross-Tier Write Hook discriminates correctly; **Gate-Sequence Hook was bypassable by rewording** — a graduate-student spawn phrased without skill keywords passed ungated.

**Usability risks.** The green `evaluate_harness` score does not by itself prove enforcement behavior (presence-based); harness self-development trips its own gates.

**Changes made (merged this cycle).**
- **PR #50** (`6bd785b`): `init_research_project.py` now *merges* harness hooks into an existing `.claude/settings.local.json` (previously skipped silently → zero enforcement on adoption) and warns on an unparseable file; honest relabel of the Claim Promotion Gate ("HARD ENFORCED" now scoped to the wired freshness/lifecycle layer vs. the Lead-run + CI count/diversity checker) plus a label-vocabulary note in `hooks_reference.md`.
- **PR #51** (`95a8403`): `enforce_gate_sequence.py` resolves required gates from the structured `subagent_type` first (prose fallback retained) — closes the rewording bypass; adds the first behavioral test coverage for the hook (8 cases). Every wired hook now has exit-code tests under `tests/`.

**Researcher review.** PI reviewed in session; approved and merged #50/#51.

**Deferred low-priority backlog.**

1. **Self-hosting over-gating (friction, maintainers only).** The harness gates its own `tests/*.py` and `AGENTS.md`/`GEMINI.md` edits (cross-tier write hook; the contract-sync PreToolUse hook blocks the second contract-file edit), so harness development requires temporarily moving the `.research-harness` marker aside. No impact on real research projects (correct behaviour there).
   - Options: (a) exempt the harness source repo via a sentinel file; (b) a dedicated `RESEARCH_HARNESS_SELF_DEV=1` bypass for the contract-sync + cross-tier hooks; (c) document the marker-move as the sanctioned harness-dev procedure.
   - Recommendation: (c) — lowest risk; (a)/(b) risk weakening or fragmenting the gate for real projects.

2. **`update_harness.py` does not refresh hooks.** Only `init_research_project.py` (re)installs hooks (now an idempotent merge after PR #50). A project updating to a harness version with new hooks will not receive them until `init` is re-run.
   - Options: (a) document "re-run `init` after an update to refresh hooks" in `README`/`README.ko` and in `update_harness.py` output; (b) add an `--upgrade-hooks` path (planned as PR5 in `claude_code_unified_implementation_plan.md`).
   - Recommendation: (a) now (one line); (b) optional later.

3. **`evaluate_harness.py` remains presence-based.** Its 30-scenario score checks file/keyword presence; behavioral enforcement is now covered by `pytest` (run in CI). The "30/30 / avg 100" headline alone does not prove behaviour.
   - Options: (a) add a one-line pointer in the report to the behavioral test suite; (b) add a few `checks=` scenarios that invoke hooks; (c) accept (CI `pytest` already gates behaviour).
   - Recommendation: (a) plus reliance on CI `pytest`.

4. **Workflow weight (by design).** 7+ mandatory gates before code, 25 skills; mitigated by the literature/model waivers (baseline-strategy and the PI gates cannot be waived). Accept as-is; revisit only if a researcher reports friction in exploratory use.

## HE-008 Detail — 2026-06-03

**Method.** Followed up on the HE-007 backlog and the direct source review. The cycle used TDD for behavior changes, then ran the deterministic checker suite and full pytest.

**Changes made.**
- `evaluate_harness.py` now labels its output as a structural harness evaluation report and prints the structural score basis plus behavioral checker-probe counts, so the 30/30 score is not mistaken for full runtime proof.
- `update_harness.py --apply --upgrade-hooks` now merges current hook registration into `.claude/settings.local.json` by reusing the project `init_research_project.py` hook merge logic. Dry-run mode explicitly does not mutate hook settings.
- The tracked `.claude/settings.local.json` is kept to portable hook registration only, and `check_harness_manifest.py` now rejects tracked local permissions.
- `docs/harness/self_hosting_development.md` documents the sanctioned source-repo self-hosting procedure without adding a permanent self-development bypass.
- README and README.ko document hook refresh, `--upgrade-hooks`, portable tracked hook settings, and the self-hosting procedure.

**Worktree audit.** `git worktree prune --verbose` found no stale metadata. Audit found 22 registered worktrees, 13 unregistered directories under `.claude/worktrees`, and 3 nested registered worktrees. No directories were deleted automatically because clean worktree removal can still disrupt another active Codex thread.

**Researcher review.** Researcher approved proceeding through the full backlog in sequence.

**Remaining gap.** The remaining worktree cleanup is an ownership/coordination task, not a harness-code defect. Remove only after confirming the corresponding thread/branch is no longer needed.

## Rules

Record every evaluation of the harness itself.

For each evaluation, include:

- scenario coverage
- failing or partial scenarios
- usability risks
- changes made because of the evaluation
- whether a researcher reviewed the evaluation
