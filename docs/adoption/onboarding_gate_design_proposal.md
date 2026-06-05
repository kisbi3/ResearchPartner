# Brownfield Onboarding — Gate-Sequence Design Proposal

Status: **PROPOSAL (awaiting PI decision).** No code or enforced machinery is
changed by this document. It proposes how the harness gate sequence should
behave when attached to research that is *already in progress*, and records the
coordinated edit set + verification gate a chosen option would require.

Author: Lead Agent (professor). Date: 2026-06-05.

---

## 1. The problem — the gate chain is greenfield-shaped

The harness's hard gate chain assumes a project starts from nothing:

```
Orient → Interview → Literature → Model → Baseline-strategy → Seed → Baseline → Validate → Execute
```

`scripts/enforce_gate_sequence.py` enforces this by **gating agent spawns**. The
prerequisite sets it requires (lines 126–236) are:

| Spawn / skill | Required gates before it may run |
|---|---|
| `seed-design` | orient, interview, literature, model, baseline_strategy |
| `graduate-student` | orient, interview, literature, model, baseline_strategy |
| `code-reviewer` | orient, interview, literature, model, baseline_strategy |
| `scientific-validator` | + baseline |

Each gate's checker reads a specific artifact:

| Gate | Checker | Artifact | Human brake? |
|---|---|---|---|
| model | `check_model_specified` | `docs/plan/model_spec.md` (+ `docs/gates/model_decision.md`) | **yes** |
| baseline_strategy | `check_baseline_strategy` | `docs/plan/baseline_strategy.md` | no |
| seed | (via seed-design reqs) | `docs/gates/seed_decision.md` | **yes** |

### Why this collides with brownfield

An already-running project **already has a model** (implemented in code), **already
has runs** (the existing results), and often **already has figures and draft
claims**. The single most natural first onboarding action — "reproduce one
existing figure from source" — requires spawning a `graduate-student`, which the
hook blocks until `model` and `baseline_strategy` are recorded.

The `model` gate is a PI brake whose checker reads `model_spec.md`. So today the
harness forces the researcher to **author a fresh greenfield model spec for a
model that is already implemented and already produced results** before it will
let any retrofit code run. That is exactly the failure
`skills/existing-research-onboarding/SKILL.md` warns against:

> Attach the harness without rewriting history, hiding uncertainty, or forcing
> old work into a false validation story.

`enforce_gate_sequence.py` currently has **zero** awareness of onboarding
(`grep onboarding scripts/enforce_gate_sequence.py` → no match). The onboarding
skill, the four `docs/adoption/*.md` templates, the task-intake category, and the
`evaluate_harness` scenario all exist — but none of them changes what the gate
hook requires. The brownfield path is recognized everywhere *except* in the one
place that actually controls execution.

---

## 2. Design principle

Onboarding must **preserve the brake, drop the false authorship.**

- Keep PI sign-off (the brake) — a human still decides the existing model and
  existing results are accepted as the working baseline.
- Stop pretending the model/seed are being *authored fresh*. In onboarding the
  model gate is satisfied by **documenting and accepting the existing model**,
  and the baseline gate by **adopting an existing result as the baseline to
  reproduce** — not by writing a greenfield spec from scratch.
- Inventory first, interpret later (the skill's core rule) must come *before*
  any gate is marked satisfied — you cannot accept a model you have not yet
  inventoried.

---

## 3. Options

### Option A — Bypass: onboarding skips model/seed gates
The onboarding classification sets `RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE`-style
relief so grad-student spawns are allowed without model/baseline_strategy.

- **Pro:** trivial; one env flag, no new machinery.
- **Con:** removes the brake entirely for the whole onboarding session. An
  adopted project would run retrofit code with *no* recorded acceptance of its
  model or baseline. This is the "hide judgment behind automation" failure. The
  bypass env var is also explicitly documented to *never* waive human gates, so
  this would contradict the existing brake contract. **Rejected.**

### Option B — Inventory-satisfied: existing artifacts satisfy the gates
Reframe the model/baseline checkers so that, in onboarding mode, an
*inventory-and-accept* artifact counts as a satisfied gate: `model_spec.md` is
filled by **documenting the existing implemented model** (not designing a new
one), and the baseline is **an existing result registered as the reproduction
target**.

- **Pro:** preserves every gate; reuses existing checkers/artifacts; the model
  brake still fires (PI still signs `model_decision.md`).
- **Con:** semantically overloads `model_spec.md` ("designed" vs "reconstructed
  from existing code") without a visible marker; a reader cannot tell whether a
  spec was authored greenfield or reconstructed during adoption. Risk of a
  reconstructed-but-wrong model spec passing as a designed one.

### Option C — New `adoption_decision.md` PI gate (recommended, combine with B)
Add **one** new human-owned decision gate specific to onboarding, then let it
satisfy the downstream model/baseline gates *in onboarding mode only*:

1. Onboarding runs **inventory first** (`audit_existing_project.py` + the four
   `docs/adoption/*.md` tables filled: intake, results inventory, retrofit plan).
2. The PI signs `docs/gates/adoption_decision.md` (`## Decision`), which records:
   the accepted existing model, the existing result chosen as the reproduction
   baseline, the first retrofit target, and the validation status assigned to
   every adopted artifact (validated/partial/unknown/failed/waived/deprecated).
3. With a signed adoption decision, `enforce_gate_sequence.py` treats `model`
   and `baseline_strategy` as **satisfied-by-adoption** for grad-student /
   code-reviewer spawns *whose purpose is retrofit/reproduction* — so the first
   retrofit can run — while `scientific-validator`'s `baseline` gate still
   requires an actual reproduction record (you must really reproduce the figure
   before any claim is validated).

- **Pro:** keeps the brake (a *new, explicit* PI sign-off rather than a
  reused-and-overloaded one); makes adoption visible and auditable; does not
  pretend a fresh model was designed; naturally routes the first retrofit into
  the existing baseline machinery (gap ④).
- **Con:** most machinery — a new gate file, a new checker, a new branch in
  `enforce_gate_sequence.py`, and a new `evaluate_harness` expectation. It is a
  CI-coupled change (see §5).

**Recommendation: Option C, with B's reframing of the model/baseline artifacts
folded in.** It is the only option that keeps the brake honest while removing the
false-authorship requirement. The cost is real machinery, but onboarding is a
first-class scenario (it has its own skill, scenario, and README section) and
deserves a first-class gate rather than an overloaded one.

---

## 4. How the gate sequence would branch (Option C sketch)

```
Existing-project onboarding classified (task-intake category #2)
  → Orient (orient_note + orient_decision: PI accepts "we are adopting X")
  → Inventory   [NEW, hard-first]:
        audit_existing_project.py  +  fill docs/adoption/{intake,results_inventory,retrofit_plan}.md
  → adoption_decision.md  [NEW PI gate]:
        accept existing model · pick reproduction baseline · first retrofit target · per-artifact status
  → with signed adoption_decision:
        model + baseline_strategy = satisfied-by-adoption (retrofit spawns allowed)
  → first retrofit (grad-student): reproduce the chosen existing result
  → scientific-validator: baseline gate still requires a real reproduction record
  → claims on adopted artifacts capped until reproduced  [gap ③, separate change]
```

Interview and Literature: in onboarding the interview reframes to "what is the
onboarding goal / which claim must survive retrofit," and Literature uses its
existing skip waiver when novelty mapping is not the point of adoption. No new
machinery needed for those two — only resident-text guidance in the skill.

---

## 5. Coordinated edit set a chosen option would require (NOT done here)

Option C touches CI-enforced machinery. The full coordinated set:

1. `scripts/check_adoption_recorded.py` — new checker for `adoption_decision.md`
   (human-owned: blank `## Decision` → not satisfied), mirroring
   `check_orient_recorded.py` / `check_model_specified.py`.
2. `scripts/enforce_gate_sequence.py` — add an onboarding branch: detect the
   onboarding context, and when `adoption_decision` is satisfied, treat
   `model` / `baseline_strategy` as satisfied-by-adoption for retrofit spawns.
3. `scripts/path_check_hooks.py` (Human-Owned Decision Gate) — add
   `docs/gates/adoption_decision.md` to the write-blocked PI-decision set, and
   `docs/gates/adoption_note.md` (or the adoption tables) as the lab-drafts side.
4. `docs/adoption/*.md` — add the `## Decision`-style PI section to whichever
   file becomes the signed gate (or add a new `adoption_decision.md`).
5. `scripts/evaluate_harness.py` — extend the `existing_project_with_old_figures`
   scenario with the new gate artifact + rule terms so CI covers it.
6. `docs/harness/capability_manifest.json` + `docs/hooks_reference.md` — register
   the new hook/gate (the Human-Owned Decision Gate catalog + wiring table).
7. `AGENTS.md` + `GEMINI.md` (byte-identical) — one line in the Human-Owned
   Decision Gate list naming the adoption gate; keep resident text short.
8. `README.md` + `README.ko.md` — update Scenario B to the inventory →
   adoption-decision → retrofit flow.
9. `scripts/init_research_project.py` — scaffold the new gate stub so fresh
   projects (and re-init) carry it.

### Verification gate (run all; all must pass before any such commit)
```
python scripts/check_contract_sync.py
python scripts/check_spawn_contracts.py
python scripts/check_harness_manifest.py
python scripts/evaluate_harness.py --fail-on-partial
python scripts/check_lineage_coverage.py --project .
pytest -q
```
(The round-1 diet regression — a missing rule term turning CI red — came from
*skipping `evaluate_harness` in this set*. It is mandatory for any
text/skill/gate change.)

---

## 6. Out of scope for this proposal (deferred gaps)

These were identified alongside the gate-sequence gap but are separate changes:

- **Gap ② — shallow scanner.** `audit_existing_project.py` only counts file
  types + greps `plt.show()`. It should auto-draft the inventory tables (figure↔
  generating-script guesses, detected seeds/params, git recency, manuscript/claim
  files) so the human corrects a draft instead of filling blank tables.
- **Gap ③ — no claim ceiling on adopted artifacts.** The status labels exist but
  nothing enforces that a manuscript claim citing an `unknown`/`partial` adopted
  artifact is capped until reproduced. Needs wiring into the claim-promotion gate.
  **STATUS: APPLIED (2026-06-05).** `check_claim_promotion_freshness.py` now, in
  adoption mode, blocks a promoted claim citing an adopted artifact marked
  `partial`/`unknown`/`failed`/`deprecated` in `existing_results_inventory.md`
  (only `validated`/`waived` pass). Wired via the existing `docs/claims/*.md`
  PreToolUse hook and the standalone audit; documented in `hooks_reference.md`.
  Verified: live hook blocks (exit 2) an unvalidated-adopted citation; validated
  citation passes; no-op off adoption mode; template placeholder rows ignored.
- **Gap ④ — baseline disconnection.** The onboarding skill/docs never reference
  `baseline-strategy` / `baseline-validation` / `baseline_registry`. Option C
  partly closes this by routing the first retrofit through the baseline gate;
  the skill text should also point there explicitly.

---

## 7. PI Decision

- **Chosen option: C** (new `adoption_decision.md` PI gate, with B's reframing
  of the model/baseline artifacts folded in). — PI, 2026-06-05.
- **Scope this round: gate branch only.** Implement the adoption decision gate
  and the satisfied-by-adoption branch in `enforce_gate_sequence.py`. Gaps ②
  (scanner depth), ③ (adopted-artifact claim ceiling), and ④ (full baseline
  wiring beyond the first-retrofit route) remain deferred to later rounds.
- Notes: keep the brake honest — the existing model/baseline are accepted only
  by a signed `adoption_decision.md`; `baseline` (real reproduction record)
  stays required for any validation.

## 8. Implementation record (2026-06-05, Option C, gate branch only)

Applied coordinated edit set:

- `docs/run_templates/adoption_decision_template.md` — new PI-owned brake stub
  (`## Decision` + accepted-model / reproduction-baseline / first-retrofit /
  per-artifact-status sections). Copied to `docs/gates/adoption_decision.md` by init.
- `scripts/_layout.py` — `adoption_decision(project)` accessor.
- `scripts/check_adoption_recorded.py` — new checker: adoption mode is active iff
  `docs/gates/adoption_decision.md` has a non-empty `## Decision`.
- `scripts/enforce_gate_sequence.py` — adoption branch: when adoption mode is
  active, `model` and `baseline_strategy` are satisfied-by-adoption; `baseline`
  and the human gates (orient/interview) are untouched.
- `scripts/path_check_hooks.py` — `docs/gates/adoption_decision.md` added to the
  human-owned write-blocked set (the lab cannot sign its own adoption).
- `scripts/init_research_project.py` — scaffolds the adoption decision stub.
- `skills/existing-research-onboarding/SKILL.md` — Gate section: inventory →
  signed adoption decision → first retrofit (routed through the baseline gate).
- `docs/harness/capability_manifest.json` — `adoption-gate` capability entry.
- `docs/hooks_reference.md`, `AGENTS.md`/`GEMINI.md`, `README.md`/`README.ko.md` —
  documented the gate and the satisfied-by-adoption rule.
- `scripts/evaluate_harness.py` — `existing_project_with_old_figures` scenario
  extended with the new gate artifact + rule terms.

**Test coverage gap (surfaced, not silently skipped):** a dedicated
`tests/test_adoption_gate.py` was *not* added this round. `tests/` is outside the
Cross-Tier Write Hook's exempt set (`docs/`, `literature/`, `scripts/`, `tools/`),
so the Lead cannot write it; the intended path is a spawned graduate-student, but
this harness-development repo's own Orient/Interview/Model gates are closed, so a
grad-student spawn is itself gate-blocked, and auto-spawning is against standing
guidance. The new behavior was instead verified manually (checker active/inactive
states; the write-block on `adoption_decision.md`; the satisfied-by-adoption
branch toggling model/baseline_strategy). Adding the unit test via a
graduate-student (or a one-off `RESEARCH_HARNESS_BYPASS_SRC_GATE` write) is a
recommended follow-up.
