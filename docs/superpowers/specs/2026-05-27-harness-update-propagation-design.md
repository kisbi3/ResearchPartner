# Harness Update Propagation Design

## Status

Active design (2026-05-27). Adds a **version stamp + selective update path**
for projects that vendored the harness, so harness evolution can reach already
-installed projects without clobbering scientific artifacts. Backward
compatible by construction: a project with no lockfile keeps working, and the
checker degrades to a "not stamped yet" report rather than failing.

## Scope

Give an installed project a deterministic, non-destructive way to pull harness
updates after the harness source evolves. The mechanism follows the established
**surface-vs-block** discipline: a read-only checker surfaces drift; an explicit
researcher-invoked command mutates, dry-run by default, never touching
project-owned files.

## Goal

Installation today is **vendoring (full copy)**, not referencing.
`scripts/install.py` copies `MANAGED_ITEMS` —
`AGENTS.md · GEMINI.md · PHYSICS.md · skills/ · docs/ · scripts/ · .claude/agents/`
— from a local checkout or a downloaded GitHub `main.zip` into each project.
The hooks in `.claude/settings.local.json` then call
`$CLAUDE_PROJECT_DIR/scripts/...`, i.e. each project runs its **own vendored
copy** of the harness logic, never a central install. A project is therefore a
frozen snapshot of the harness at install time, with no link back to the source.

Three concrete gaps follow:

- **No version stamp.** The `.research-harness` marker is pure prose — no
  version, no commit, no content hashes. `_layout.LAYOUT_VERSION` is a
  directory-schema version, not stamped into the project and not a release
  version. Nothing can answer "which harness is this project on?"
- **No safe update path.** `install.py` has two modes: without `--force` it
  *refuses* when any managed item exists (cannot update); with `--force` it does
  `rmtree(target)` then `copytree` per item. Because `docs/` is a managed item
  **and the researcher's gate artifacts live under `docs/`** (`docs/gates/`,
  `docs/plan/model_spec.md`, `docs/process/...`), a `--force` re-install
  **deletes scientific artifacts**. This is a latent data-loss bug independent
  of this design.
- **Re-running `init` only half-helps.** `init_research_project.py` is
  additive-only (`_copy_if_absent`) and never manages `scripts/`. Re-init picks
  up *new* doc templates but nothing about changed scripts/skills/`AGENTS.md`.

These are one missing primitive: a **per-project content stamp** plus a
**precise harness-owned/project-owned boundary** that a selective updater and a
drift checker can both read.

## Design

### Version stamp — `harness.lock.json` (project root, committed)

Keep the marker a pure locator. A sibling lockfile records the realized
snapshot the harness gave this project:

```json
{
  "lock_schema": 1,
  "harness_version": "3.x",
  "harness_commit": "c089be1",
  "installed_at": "2026-05-27T00:00:00Z",
  "updated_at": "2026-05-27T00:00:00Z",
  "files": {
    "scripts/workflow_hooks.py": "sha256:…",
    "AGENTS.md": "sha256:…",
    "docs/hooks_reference.md": "sha256:…"
  }
}
```

`harness_commit` is best-effort: captured when the source is a git checkout,
omitted for the zip-download path (version string is the reliable anchor). The
lockfile is **committed** — it is part of the project's reproducibility record
("this project runs harness vX, commit Y"), not session-local state. It is the
baseline `L` for 3-way comparison.

### Ownership boundary — shipped owned-paths manifest

The harness ships an authoritative manifest of its own paths
(`docs/harness/owned_paths.json`):

```
owned:  scripts/**/*.py · skills/** · .claude/agents/** ·
        AGENTS.md · GEMINI.md · PHYSICS.md ·
        docs/run_templates/** · docs/hooks_reference.md ·
        docs/orchestration_protocol.md · docs/harness/** ·
        docs/literature/*_template.md
```

**Operative rule: update touches only `owned ∪ {paths recorded in the
lockfile}`.** Project-owned trees — `docs/gates/`, filled `docs/plan/`,
`docs/process/`, `literature/` instances, `src/`, `outputs/`, `claims/`,
`evidence/`, `.claude/settings.local.json`, the marker, the lockfile itself —
are absent from `owned`, so they are **never touched by construction**. The
same manifest, applied to `install.py --force`, fixes the `docs/`-clobber bug:
`--force` overwrites only owned paths, never the whole `docs/` tree.

Doc instances vs templates are handled by listing *templates* as owned
(`docs/run_templates/**`, `docs/literature/*_template.md`) while the *instances*
they seed (`docs/plan/model_spec.md`, `literature/index.md`,
`docs/literature/literature_review_plan.md`, `docs/literature/replanning_memo.md`)
are simply not in `owned` and so are left alone.

### Selective update — 3-way comparison

For each path in `owned ∪ lockfile.files`, with `H` = hash in the new harness
source, `L` = hash in the lockfile, `P` = hash currently in the project:

| Condition | Action |
|---|---|
| `P==L`, `H≠L` (unmodified locally, harness changed) | **UPDATE** → write `H`, refresh lock |
| `P==L`, `H==L` | no-op (current) |
| `P≠L`, `H≠L` (locally modified **and** harness changed) | **CONFLICT** → keep `P`, write `path.harness-new` sidecar, report |
| `P≠L`, `H==L` (locally modified, harness unchanged) | keep `P` (respect local edit) |
| not in lock, exists in harness | **ADD** → write `H`, add to lock |
| in lock, removed from harness | **REMOVED** → report only (no auto-delete) |
| in lock, deleted locally | report only |

Safety invariants:

1. Never touch a path outside `owned ∪ lockfile.files` — scientific artifacts
   are safe by construction.
2. Never silently overwrite a locally modified harness file — always surface a
   conflict via a `.harness-new` sidecar.
3. Never auto-apply upstream deletions — surface only.
4. **Dry-run is the default; `--apply` is required to mutate.** Surface before
   act.

### Surface vs block split

- **`scripts/check_harness_version.py`** (read-only, no network): reports
  lockfile presence + version, and how many owned files differ from their
  recorded hash (i.e. local modifications since install). Always runnable;
  wireable into CI / stage-checkpoint surfacing.
- **Upstream delta** ("N behind") is computed by
  `scripts/update_harness.py --dry-run --source <harness>`, which has `H` in
  hand. The checker never needs the harness source — the roles are split so the
  always-on checker stays dependency-free.

## Backward compatibility

- **Legacy projects (no lockfile).** `L` is absent, so the first cycle cannot
  distinguish "modified since install" from "as installed." `update_harness.py
  --adopt` stamps the current owned-file state as `L` once; from then on 3-way
  works normally. Known limitation: the first stamp cannot recover pre-existing
  local edits.
- **Self-usage (this repo is the harness source).** `update_harness.py` is a
  no-op / refuses when `source == target`. The harness repo does not commit a
  `harness.lock.json`, and update requires a lockfile, so it naturally declines.
- **Checker on an unstamped project** exits 0 with a "not stamped; run install
  to stamp" report — never a hard failure, so legacy CI is untaxed.

## Build sequence

| Step | Content | Enforcement change | When |
|---|---|---|---|
| **1. Stamp + drift surfacing** | `docs/harness/owned_paths.json`; `install.py` authors `harness.lock.json` (version + best-effort commit + per-file sha256); **`install.py --force` honors the ownership boundary (data-loss fix)**; `scripts/check_harness_version.py` (read-only); tests + CI + README / README.ko | **none** — purely additive plus a safety fix; checker degrades to a report on unstamped projects | now |
| **2. `update_harness.py`** | 3-way selective updater; dry-run default, `--apply`; `.harness-new` conflict sidecars; ADD / REMOVED surfacing; lock refresh; `--adopt` for legacy projects | new opt-in mutation (researcher-invoked, never silent) | after Step 1 stamp exists |
| **3. (optional) upstream-aware + ergonomics** | "N behind" via a shipped version manifest / source probe; `/update-harness` skill or command; wire drift into stage-checkpoint surfacing | — | after Step 2 |

Step 1 is safe and identical regardless of the final shape of Steps 2–3, so
sequencing loses nothing — same argument as the domain-workspaces build order.

## Validation

Step 1 acceptance — all green:

```powershell
python -m pytest tests -q
python scripts\check_harness_manifest.py
python scripts\check_spawn_contracts.py
python scripts\check_contract_sync.py
python scripts\evaluate_harness.py --fail-on-partial
```

Plus:

- A fresh `install.py` into an empty target writes `harness.lock.json` whose
  `files` hashes match the installed bytes.
- `install.py --force` over a project with content under `docs/gates/`,
  `docs/plan/`, `docs/process/` refreshes owned files but **leaves those
  project-owned artifacts intact** (regression test for the data-loss bug).
- `check_harness_version.py` on a stamped, unmodified project reports zero
  local modifications and exits 0; after editing one owned file it reports that
  file and still exits 0 (surfacing, not blocking) — or a chosen nonzero code
  if drift is promoted to a gate later.
- `check_harness_version.py` on an unstamped (legacy) project exits 0 with a
  "not stamped" report.

## Risks and caveats

- **Ownership manifest drift.** `owned_paths.json` must track real harness file
  moves; a stale manifest silently stops updating a relocated file. Keep it
  validated against `MANAGED_ITEMS` (and ideally the capability manifest) so the
  boundary cannot rot unnoticed.
- **First-stamp blindness on legacy projects.** `--adopt` cannot recover edits
  made before the lockfile existed; document this and prefer adopting from a
  clean checkout where possible.
- **Lockfile churn in diffs.** Per-file hashes change on every update; keep the
  lockfile readable (sorted keys, one path per line) so review stays tractable.
- **Do not centralize prematurely.** Vendoring preserves the harness's
  committed-reproducible thesis (a project pinned to commit Y still runs years
  later). This design keeps self-containment and makes updates opt-in; it does
  **not** move projects onto a shared central install.
- **`AGENTS.md`/`GEMINI.md` stay byte-identical.** They are owned files; an
  update that touches one must touch both. `check_contract_sync.py` remains the
  backstop.
```
