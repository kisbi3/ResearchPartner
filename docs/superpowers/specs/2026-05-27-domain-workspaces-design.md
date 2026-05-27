# Domain Workspaces Design

## Status

Active design (2026-05-27). Adds an optional **domain axis** on top of the
Layout v3 single-flat-tree assumption in `scripts/_layout.py`. Backward
compatible by construction: a project with no `domains/` directory behaves
exactly as today.

## Scope

Let a research project organize its working directories along a **domain
(bounded-context) axis** instead of only a **file-type axis**, and give each
domain a co-located, typed manual that an agent reads before working in it.

A *domain* is a self-contained unit of research work:

- a **reproduction** target (reproduce Fig/Eq/number from a specific paper),
- a parallel **thread** (e.g. 1D baseline vs 2D extension worked in parallel),
- a **subproblem**, or
- an **integration** workspace that rolls several domains together.

## Goal

Today `_layout.py` defines one flat tree per `.research-harness` marker:
`src/` (all code), `outputs/` (all results), `docs/{gates,plan,process,...}`
(all control docs). The division axis is "what kind of file is this." Two
recurring needs are forced to share one undifferentiated space:

- **Reproduction.** A reproduced result's ground truth is an *external
  published value*; its provenance class differs from novel work. Mixed into
  flat `src/`+`outputs/`, no checker can tell a reproduction figure from a
  novel-result figure, and the reproduced baseline cannot be cleanly frozen as
  a reference (artifact-freshness treats it like live work).
- **Split-and-integrate.** Breaking a project into parallel threads currently
  means sibling markers (full schema duplication, zero aggregation).
  Integration is exactly where a joint claim can exceed what any single
  thread's evidence supports, with no checker watching the seam.

Both are the same missing primitive: a **typed domain workspace with a
co-located manual** that an agent (and, later, a checker) can read.

## Architecture: three tiers

| Tier | Location | Holds | Gate scope |
|---|---|---|---|
| **Project spine** (singular) | project root `docs/`, `literature/` | `research_question` · orient · interview; shared literature corpus; workflow dashboard; manuscript-level claim ledger; retrospective | orient / interview / literature gates fire **once per project** |
| **Domain workspace** (one per domain, self-documenting) | `domains/<name>/` | `model_spec` · code · outputs · local validation · local claims · **`README.md` manual (typed header)** | model / baseline / validation gates fire **per domain** |
| **Integration layer** | manuscript claim ledger (spine) | imports domain claims as external evidence; re-runs claim-promotion over the union | **integration gate** (new checker) |

## Skill-order split (key consequence)

The required research order splits across tiers instead of being one chain:

- **Project spine, once per project:** `task-intake -> professor-interview ->
  literature-review`
- **Per domain, repeated:** `model-specification -> baseline-strategy ->
  baseline-validation`

This makes the two motivating scenarios fall out for free:

- A **reproduction** domain runs model (= the paper's model) -> baseline
  (= reproduce) -> validation (= match the published value within tolerance).
  Manual header: `type=reproduction, ground-truth=external-paper:<id>`.
- A **thread** runs its own model -> baseline -> validation inside the domain.
  Manual header: `type=thread, depends-on=..., integrates-into=...`.
- The project decides "why it exists" (interview) and "what literature it
  shares" exactly once.

## Domain layout

```text
<project>/                     # single .research-harness marker; spine intact
  docs/                        # SPINE: gates/(orient,interview), literature/, claims/(manuscript ledger), process/
  literature/                  # shared corpus
  src/  outputs/               # implicit DEFAULT domain = today's flat layout (back-compat)
  domains/
    repro-smith2024/
      README.md                # typed manual: type=reproduction, ground-truth=external-paper:smith2024, pass=...
      src/  outputs/
      plan/model_spec.md  plan/baseline_strategy.md
      claims/                  # domain-local claims
    2d-extension/
      README.md                # type=thread, depends-on=..., integrates-into=...
      src/  outputs/
      plan/  claims/
```

## Domain manual (typed README)

Each `domains/<name>/README.md` carries a typed header plus a mini run-packet:

- `type`: `reproduction | thread | subproblem | integration`
- `purpose`: one line
- `ground-truth`: `internal-validation | external-paper:<id> | analytical-limit`
  — the provenance class
- `pass/fail`: success criteria for this domain
- `units` / `assumptions`: local to this domain
- `relations`: `depends-on:` / `integrates-into:`
- `claim-ceiling-cap`: the strongest claim this domain may assert

**Surface-first, blocking-later.** In Step 1 the manual is *surface guidance*:
agents read it, checkers ignore it. A later step may promote *presence +
well-typed header* to a deterministic check, then enforce type-specific rules
on top (e.g. every figure in a `type=reproduction` domain must cite its
external paper and have a `reproduction_log` row with a match criterion).

## Backward compatibility

`_layout.py` gains a domain resolver:

- `domain_names(project)` — sorted subdirectory names under `domains/`, or `[]`.
- `domains(project)` — domain roots to iterate. If `domain_names` is non-empty,
  the `domains/<name>/` roots; **otherwise `[project]`** — one implicit default
  domain equal to the project root, i.e. today's flat layout.

All domain-iterating code returns `[default]` for legacy projects, so existing
tests, CI, and this repository's own usage artifacts are unchanged. This is the
seam that keeps Step 1 a zero-enforcement-change refactor.

## Integration gate (anti-laundering)

At the integration tier, domain claims are imported into the manuscript ledger
as external evidence and claim-promotion re-runs over the union with two
invariants:

- a manuscript claim's ceiling is `<=` what the union of imported domain
  evidence supports;
- a **generalization** spanning domains must cite evidence from `>= 2` domains
  (otherwise it is one domain's claim relabeled).

This is the deterministic bolt that stops claim laundering at the seam where
per-domain lineage checks, run in isolation, each pass.

## Build sequence

| Step | Content | Enforcement change | When |
|---|---|---|---|
| **1. Foundation** | domain resolver + default-domain back-compat in `_layout.py`; `scripts/scaffold_domain.py`; `docs/run_templates/domain_manual_template.md`; minimal domain listing in the workflow graph (surfacing only); tests; README / README.ko | **none** (checkers iterate domains, which is `[default]` for legacy -> identical results) | now |
| **2. Per-domain model/baseline/validation** | relocate `model_spec`/`baseline_strategy`/validation into the domain; split the required skill order; gate checkers gain `--domain`; project stage = aggregate over domains | gates become domain-aware | design against a first real domain |
| **3. Domain claims + integration gate** | domain-local claims; new integration checker enforcing the anti-laundering invariants | claim/lineage become domain-aware | requires `>= 2` domains to test |

Each step ships as a PR with its own checker (where applicable) + tests + CI +
scientific-validator coverage, matching the established rhythm. Step 1 is safe
and identical regardless of the final tier shape, so sequencing loses nothing.

## Validation

Step 1 acceptance — all green:

```powershell
python -m pytest tests -q
python scripts\check_harness_manifest.py
python scripts\check_spawn_contracts.py
python scripts\check_contract_sync.py
python scripts\evaluate_harness.py --fail-on-partial
```

Plus: a legacy flat project resolves to one default domain; a `domains/`-bearing
project enumerates its domains; `scaffold_domain.py` produces a typed manual
from the template.

## Risks and caveats

- Steps 2-3 refactor the enforcement spine (`_layout.py` consumers, claim and
  lineage checkers). Do **not** design them abstractly — anchor to a real
  domain so gate semantics and the claim-aggregation rule are chosen against
  reality.
- The manual must stay lightweight or it becomes ceremonial. Start as surface
  guidance; only promote header presence to a blocking check once real use
  shows it earns enforcement.
- Keep `AGENTS.md` slim. Domains are *optional* in Step 1, so Step 1 updates
  `README.md` / `README.ko.md` only. The skill-order split touches
  `AGENTS.md`/`GEMINI.md` (byte-identical) at Step 2, not before.
