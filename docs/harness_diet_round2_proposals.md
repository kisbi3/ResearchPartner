# harness diet — §6 high-risk proposals (round 2)

Read-only reconnaissance for the §6 items the PI authorized to "착수" on 2026-06-05.
**No files were mutated this round.** The recon found that the harness-legacy-scan
report under-rated *registry / CI / generator coupling*: three items the report (and
the PI prompt) treated as "low-risk reversible" are in fact bound to CI-enforced
machinery and cannot be applied as drop-in edits. Each item below states the **true
coupling**, the **coordinated edit set** a safe change actually requires, and the
**verification gate** (the harness's own checkers) that must pass.

## The coupling that bit (why these are not low-risk)

The harness has a self-verification spine that binds skills/agents/hooks to registries
and CI:

- `scripts/evaluate_harness.py` — **CI gate** (`.github/workflows/harness-checks.yml` runs it with `--fail-on-partial`). It enumerates exact skill paths across ~12 scenarios (e.g. `skills/research-plan-review/SKILL.md`, `skills/researcher-review-loop/SKILL.md`, `skills/code-reviewer/SKILL.md`, `skills/cache-log-auditor/SKILL.md`). Archiving any enumerated skill turns CI red.
- `docs/harness/spawn_contracts.json` + `scripts/check_spawn_contracts.py` — declare `"skill": "skills/<role>/SKILL.md"` per leaf role and validate that `.claude/agents/<role>.md` frontmatter `tools` == `allowed_tools`. The skill path must exist.
- `docs/harness/capability_manifest.json` + `scripts/check_harness_manifest.py` — a `hook_registry` lists every wired hook (id/command/script) and cross-checks it against `.claude/settings.local.json`; `workflow_hooks.py pre/post` is registered on the Write|Edit and Bash matchers (manifest lines ~194/234/274).
- `scripts/install_skills.py` — **generator**: copies `skills/<name>/SKILL.md` → `.claude/commands/<name>.md`, `.agents/skills/`, `.codex/skills/` from a `SKILLS = [...]` list. The `.claude/commands` byte-identical copies are *build output*, not source.

**Verification gate for ANY of these changes** (run all; all must pass before commit):
```
python scripts/check_contract_sync.py          # AGENTS == GEMINI + word budget
python scripts/check_spawn_contracts.py         # leaf role <-> agent <-> skill consistency
python scripts/check_harness_manifest.py        # capability manifest + hook registry coverage
python scripts/evaluate_harness.py --fail-on-partial   # CI scenario coverage
python scripts/check_lineage_coverage.py --project .   # broken-edge / lineage
pytest -q                                        # repo tests (incl. test_check_spawn_contracts.py)
```

---

## Item 1 — CONVERT code-reviewer / cache-log-auditor (skill+agent fold)

- **Report claim**: UPHOLD / low-risk / reversible (fold 48- and 81-line skills into the 11-line agent stubs).
- **True coupling**: `spawn_contracts.json` declares `"skill": "skills/code-reviewer/SKILL.md"` and `.../cache-log-auditor/SKILL.md`; `evaluate_harness.py` enumerates both; `capability_manifest.json` references both; `install_skills.py` `SKILLS` distributes both to 3 CLIs.
- **Coordinated edit set required to do it safely**:
  1. Move skill body into `.claude/agents/<role>.md` (preserve frontmatter `tools: Read, Grep, Glob` — load-bearing for author≠validator).
  2. Decide the skill's fate: either (a) keep `skills/<role>/SKILL.md` as a thin pointer to the agent (no net dedup — pointless), or (b) archive it AND update `spawn_contracts.json` (drop/redirect the `"skill"` field), `evaluate_harness.py` (remove the skill-path expectations), `capability_manifest.json`, and the `install_skills.py` SKILLS list.
  3. Run the full verification gate.
- **Risk**: medium. Editing `evaluate_harness.py` changes what CI considers "covered" — the adversarial review's exact warning. Reversible only if the registry edits are reverted together.
- **Recommendation**: defer unless the goal is worth a coordinated registry+CI change. The duplication is on-demand (not a per-session tax); the only payoff is less maintenance drift. **Low payoff, real coupling → not worth it now.**

## Item 2 — MERGE research-plan-review + researcher-review-loop

- **Report claim**: UPHOLD / "safest merge, no enforcing checker."
- **True coupling**: there is no *gate* checker, but BOTH are enumerated by `evaluate_harness.py` (scenarios at lines 32/50/85/127/153/190/209…) and distributed by `install_skills.py`; `researcher-review-loop` also appears in `workflow_map.json` and `run_baseline_validation.py`.
- **Coordinated edit set**: create the merged skill; update every `evaluate_harness.py` scenario that names either source to the merged path; update `install_skills.py` SKILLS; update `run_baseline_validation.py` and docs; archive the two originals.
- **Risk**: medium (many `evaluate_harness.py` touch-points; a missed one fails CI). Genuinely no hard-gate desync, so it is the *least* dangerous merge — but still a coordinated CI edit, not a drop-in.
- **Recommendation**: viable as a deliberate, test-gated change. Best first candidate **if** the PI wants one consolidation done properly with the gate run after.

## Item 3 — MERGE claim-to-evidence + scientific-verification-before-claim

- **Report verdict**: NEEDS_HUMAN (hard claim-promotion gate ladder).
- **True coupling**: the HARD claim-promotion gate (`path_check_hooks.py` blocks `docs/claims/*.md` writes without a resolved Finding Lifecycle) parses a specific lifecycle/ladder structure. The two skills teach *different* ladders (7-rung vs 11-type). Both are enumerated by `evaluate_harness.py`. `check_claim_promotion.py` / freshness checker key on the produced structure.
- **Coordinated edit set + test**: pick the ladder the live checker actually parses; merge red-flag lists; rewrite to one lifecycle structure; update `evaluate_harness.py`; then **prove** with a positive+negative claim-write test (a well-formed claim passes the gate; a malformed one is blocked) before trusting it.
- **Risk**: **high**. A ladder/lifecycle mismatch either blocks every claim write or lets a malformed lifecycle through.
- **Recommendation**: PI decision + dedicated tested change only. Do not bundle with anything else.

## Item 4 — CONVERT graduate-student / scientific-validator / peer-review-professor

- **Report verdict**: SOFTEN / NEEDS_HUMAN.
- **True coupling**:
  - `graduate-student`: the skill carries the spawn-log-row protocol that `check_src_write_authorization.py` depends on (a `.py` write is authorized only with a fresh grad-student spawn-log row). Fold must preserve this byte-for-byte or legitimate grad writes start blocking.
  - `scientific-validator`: verdict-ceiling text is cross-referenced from AGENTS.md (L26) and other skills; references must move in lockstep.
  - `peer-review-professor`: `check_peer_review_invocation.py` detects the role by **role-name / skill-path strings**; renaming or relocating the skill path can silently disable the meeting-only gate.
- **Risk**: **high** (silent gate failure modes).
- **Recommendation**: PI decision + per-role tested change. The peer-review one especially needs the hook's detection strings updated and re-tested in the same commit.

## Item 5 — commands → thin stub  *(report's DELETE/SOFTEN candidate)*

- **Recon overturns the report**: `.claude/commands/*.md` are **generated artifacts** (`install_skills.py` copies from `skills/`). The byte-identical duplication is intentional multi-CLI distribution (Claude `.claude/commands`, Antigravity `.agents/skills`, Codex `.codex/skills`). Hand-editing the commands is reverted on the next install and would desync the three CLI targets.
- **Risk**: changing this means changing the **generator's distribution strategy** (emit stubs for every CLI), affecting Claude + Antigravity + Codex equally.
- **Recommendation**: **drop this item.** Not legacy cruft; it is working build output. If maintenance drift is a concern, the fix is in `install_skills.py`, not the artifacts — and that is a distribution-architecture decision, not a diet.

## Item 6 — Remove dead workflow_hooks wiring  *(report §3.10, UPHOLD)*

- **True coupling**: `capability_manifest.json` hook_registry registers `workflow_hooks.py pre/post` on the Write|Edit and Bash matchers (the same slots that are dead, since `workflow_hooks.main()` returns 0 for non-Agent tools). Removing the 3 entries from `settings.local.json` without editing the manifest registry fails `check_harness_manifest.py` (wired≠registry). Re-running `init_research_project.py` would also re-add them unless the source registry changes.
- **Coordinated edit set**: drop the 3 dead entries from `settings.local.json` **and** the matching `hook_registry` rows in `capability_manifest.json` (or move them to `known_uncovered_wired_hooks`), then re-run init and the manifest checker.
- **Risk**: low *behaviorally* (the wiring is provably dead — `workflow_hooks.py` L281-282), but it is a **hook-config + manifest** edit, which the diet was scoped to avoid. Still the cleanest of the six.
- **Recommendation**: safe to do as a deliberate paired edit (settings + manifest) with the manifest checker as the gate. Good second candidate after Item 2 if the PI wants tangible cleanup.

---

## Bottom line / recommended next round

- **Drop**: Item 5 (generated artifact, not cruft) and figure-provenance narrowing (DOWNGRADE→KEEP from round 1).
- **Do, one at a time, each with the full verification gate run after**: Item 6 (settings+manifest paired edit) → Item 2 (the no-hard-gate merge). These are the two with real payoff and bounded, testable coupling.
- **PI decision + dedicated tested change**: Items 1, 3, 4 — higher coupling, lower payoff (Item 1) or hard-gate/silent-failure risk (Items 3, 4).
- **Correction to the audit**: the harness-legacy-scan report measured *content duplication* but not the *registry/CI/generator graph*. Any future diet must treat `evaluate_harness.py`, `spawn_contracts.json`, `capability_manifest.json`, and `install_skills.py` as the coupling that decides whether a change is low-risk.
