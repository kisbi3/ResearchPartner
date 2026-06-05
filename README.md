# Research Partner: Physics Research Harness

Research Partner is a repository harness for AI-assisted physics work. It keeps the research chain visible, blocks unsupported claim promotion, and leaves scientific judgment with the researcher instead of hiding it behind automation.

## What It Is

Research Partner protects the chain:

```text
physical assumptions -> model definition -> analytical checks -> numerical implementation -> validation -> figures -> manuscript claims
```

The workflow loop is:

```text
Orient -> Interview -> Specify -> Seed -> Validate -> Execute -> Evaluate -> Review -> Retrospect
    ^                                                                                 |
    +----------------------------- Evolutionary Loop ---------------------------------+
```

Each stage writes durable artifacts under `docs/`, `literature/`, `outputs/`, or the live workflow files. `workflow_hooks.py` automatically records agent spawns, while `/sync-workflow` (`python scripts\sync_workflow.py --project <project-dir>`) is the primary path for refreshing live workflow data and `workflow_map.live.json`. `generate_workflow_map.py` is for rebuilding the HTML shell when needed; it is not the main state-update path.

## Install

Prerequisites:

- Python 3.10 or newer available as `python`.
- A local research project directory.
- Git is recommended for checkpointing, but not required.
- Test and CI dependencies are declared in `requirements.txt`.

Install into the current project root:

```powershell
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/kisbi3/ResearchPartner/main/scripts/install.py').read())"
python scripts\init_research_project.py
```

Verify the installation:

```powershell
python -m pip install -r requirements.txt
python scripts\evaluate_harness.py --fail-on-partial
python scripts\check_harness_manifest.py
python scripts\check_spawn_contracts.py
python scripts\check_contract_sync.py
python scripts\check_harness_version.py
```

Install writes `harness.lock.json` with owned-file hashes so a project can report its installed harness stamp and local harness edits. `install.py --force` refreshes harness-owned files only; project-owned research artifacts under `docs/gates/`, `docs/plan/`, and `docs/process/` are preserved. Use `python scripts\update_harness.py --project <project-dir> --source <harness-source>` to dry-run a selective update; add `--apply` to write harness-owned updates, review `.harness-new` sidecars for conflicts, then run `python scripts\init_research_project.py` from the project root to refresh live hooks. Or add `--upgrade-hooks` with `--apply` to merge hook registration during the update. Use `--adopt` only to stamp an unstamped legacy project.

Start the first run by asking the assistant to begin with task intake. The project marker `.research-harness`, `docs\process\live_workflow_diagram.md`, literature workspace, project packet, and `outputs/` are scaffolded by initialization. Use `/sync-workflow` after gate, evidence, or lineage changes.

The live enforcement hooks live in `.claude/settings.local.json`. If that file does not exist, initialization writes it; if it already exists (common when adopting the harness into a project that already uses Claude Code), initialization **merges** the harness hooks into it — preserving your existing permissions and custom hooks, and skipping any harness hook already present (idempotent). The tracked harness copy of this file should contain portable hook registration only, not machine-local permissions. If the file exists but cannot be parsed, initialization leaves it untouched and prints a warning that the hooks were not installed. Re-run `python scripts\init_research_project.py` after editing the file to install them.

## Using It

The assistant should begin every research task with `skills/task-intake/SKILL.md`, then follow the required research order for new model, simulation, analysis, manuscript claim, or reproduction work:

```text
task-intake -> professor-interview -> literature-review-planning -> model-specification -> baseline-strategy -> seed-design -> baseline-validation
```

Scenario A, new model or simulation:

1. Capture the research question, assumptions, units, and first professor question.
2. Review or explicitly waive literature. A literature waiver lowers the claim ceiling to `interpretation`.
3. Specify the model. A model waiver lowers the claim ceiling to `observation`.
4. Choose baseline strategy, design seed tasks, validate the baseline, then execute the smallest iteration that can change interpretation.
5. Record evidence, run `/sync-workflow`, and promote claims only through the claim-promotion gates.

Scenario B, existing project (brownfield onboarding):

1. Run `python scripts\audit_existing_project.py <project-root>` to inventory scripts, figures, outputs, and validation gaps. It also drafts the adoption inventory — one row per detected figure with a guessed generating script, input data, seed/RNG sites, and git recency (`--write-drafts` writes these as `docs/adoption/*.draft.md`, never overwriting an edited file).
2. Initialize the harness in place, preserving project files, and correct the drafted `docs/adoption/*` inventory (intake, results inventory, retrofit plan).
3. The PI signs `docs/gates/adoption_decision.md`, accepting the existing model and choosing one existing result as the reproduction baseline. This puts the project in adoption mode: the model and baseline-strategy gates become satisfied-by-adoption, so the first retrofit can run without authoring a from-scratch model spec. The baseline gate is not waived — the chosen result must actually be reproduced before any claim on it is validated.
4. Use `/sync-workflow` to rebuild live state from artifacts.
5. Use validation, provenance, lineage, and claim checks before strengthening old figures or manuscript text.

Optional domain workspaces let one marked project carry named `domains/<name>/` areas for a reproduction, thread, subproblem, or integration workspace. Step 1 keeps all project-level gates, claim checks, lineage checks, and provenance checks unchanged; a project without `domains/` still resolves to the project root as its default domain.

Platform routing:

| Platform | Reads | Notes |
|---|---|---|
| Codex / Copilot-style agents | `AGENTS.md` | Resident contract, kept under a word budget |
| Gemini CLI | `GEMINI.md` | Must stay byte-identical with `AGENTS.md` |
| Claude Code | `AGENTS.md` or project `CLAUDE.md` | Project hooks and `.claude/agents/<role>.md` apply when installed |
| Slash commands | `python scripts\install_skills.py [--global]` | Installs skills for Claude Code, Gemini/Antigravity-cli, and Codex surfaces |

## Research Model

Research Partner is modelled on a research group: you own a professor-led lab. The **PI** is you, the human researcher: you own the science and the gate decisions. The **Lead Agent** is the professor — the main conversation context that owns researcher dialogue, scientific judgment, and is the *only* role that spawns subagents. The lab members are spawned leaf agents.

A typical iteration reads as a lab cycle, not a checklist: PI request -> professor's question -> lab member runs it -> independent validation -> professor's summary -> PI decision. Each arrow leaves a durable artifact, and the final decision is one only you can sign (see the brake below).

**The brake (Human-Owned Decision Gate).** The harness's #1 principle — leave scientific judgment with the researcher — is enforced, not just suggested. The decision files `docs/gates/{orient,interview,model,seed}_decision.md` (and the skip waivers) are write-blocked for *every* agent: the lab drafts proposals in the matching note/spec files, but only you record the decision. Those gates stay closed — and the bypass env vars never waive your sign-off — until you fill in `## Decision`.

Leaf agents are spawned directly by the Lead (by `subagent_type`):

| Leaf agent | Purpose |
|---|---|
| Graduate Student | Writes **and runs** code for one bounded task (parallelizable); reports evidence and its interpretation as hypotheses; never pronounces the binding verdict |
| Code Reviewer | Reads the code statically — correctness, spec conformance, reproducibility hygiene; does not run it |
| Scientific Validator | Independently re-runs and checks results against pre-set criteria; does not modify code or strengthen claims |
| Cache-Log Auditor | Audits logs, cache, and output hygiene mechanically |
| Workflow Manager | Refreshes workflow + lineage state; reports gate status and broken edges |
| Peer-Review Professor | Single-shot adversarial review inside `meeting --scope review` or `--scope full` |

Author ≠ validator: the graduate student that writes code never certifies its own result — an independent Scientific Validator pronounces pass/fail against the criterion you locked at the model/seed gate.

The Lead Agent uses nine stances as mental modes, not extra agents: Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, and Architect. See `docs/orchestration_protocol.md` for spawn blocks, stance details, and completion-conference rules.

## Reference

Commands:

| Need | Command | Purpose |
|---|---|---|
| Install harness | `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/kisbi3/ResearchPartner/main/scripts/install.py').read())"` | Install managed harness files into the current project |
| Init project | `python scripts\init_research_project.py --project <project-dir>` | Mark and scaffold a research project |
| Scaffold domain workspace | `python scripts\scaffold_domain.py --project <project-dir> --name <slug> --type reproduction` | Add an optional `domains\<slug>\` workspace and typed manual without moving project-level gates |
| Check domain manifest | `python scripts\check_domain_manifest.py --project <project-dir>` | Validate opted-in domain manuals; dormant when `domains/` is absent |
| Audit existing project | `python scripts\audit_existing_project.py <project-root>` | Inventory scripts/figures/outputs/gaps and draft the adoption inventory (guessed figure→script→data, seed sites, git recency); `--write-drafts` for `docs/adoption/*.draft.md` |
| Evaluate harness | `python scripts\evaluate_harness.py --fail-on-partial` | Check scenario coverage; partial now fails CI |
| Check harness stamp | `python scripts\check_harness_version.py --project <project-dir>` | Report installed harness stamp and locally modified owned files |
| Update vendored harness | `python scripts\update_harness.py --project <project-dir> --source <harness-source> [--apply] [--upgrade-hooks]` | Dry-run or apply non-destructive harness-owned updates; conflicts become `.harness-new` sidecars; use `--upgrade-hooks` with `--apply` to refresh hooks |
| Install test dependencies | `python -m pip install -r requirements.txt` | Install `pytest` and `PyYAML` |
| CI harness checks | `.github/workflows/harness-checks.yml` | Run deterministic gates on push and pull request |
| Sync live workflow | `python scripts\sync_workflow.py --project <project-dir> [--validate-edges]` | Refresh gate status, lineage, and live JSON |
| Rebuild workflow HTML | `python scripts\generate_workflow_map.py [--central]` | Recreate the dashboard shell when needed |
| Serve workflow map | `python scripts\serve_workflow_map.py --project <project-dir>` | Serve the workflow dashboard locally |
| Check manifest | `python scripts\check_harness_manifest.py` | Validate capability manifest, hook registry, and portable hook paths |
| Check spawn contracts | `python scripts\check_spawn_contracts.py` | Validate leaf agent definitions, tools, and single-spawner contract |
| Check contract sync | `python scripts\check_contract_sync.py` | Enforce `AGENTS.md` == `GEMINI.md` and resident word budget |
| Check orient gate | `python scripts\check_orient_recorded.py --project <project-dir>` | Require task-intake artifact before downstream work |
| Check interview gate | `python scripts\check_interview_recorded.py --project <project-dir>` | Require crystallized research question and agreed direction |
| Check literature gate | `python scripts\check_literature_reviewed.py --project <project-dir>` | Require ready/waived literature status |
| Check model gate | `python scripts\check_model_specified.py --project <project-dir>` | Require model definition or waiver |
| Check baseline strategy | `python scripts\check_baseline_strategy.py --project <project-dir>` | Require variation/new-model decision and target |
| Check baseline gate | `python scripts\check_baseline_gate.py --project <project-dir>` | Require baseline pass or explicit waiver |
| Check claim promotion | `python scripts\check_claim_promotion.py --project <project-dir> --target mechanism` | Gate claim-ceiling promotion |
| Check claim freshness | `python scripts\check_claim_promotion_freshness.py --project <project-dir>` | Check claim documents for stale or candidate-only support |
| Check lineage coverage | `python scripts\check_lineage_coverage.py --project <project-dir> [--strict]` | Find unsupported claims and broken lineage expectations |
| Check figure provenance | `python scripts\check_figure_provenance.py --root <project-dir>` | Require traceable figure provenance |
| Check session resumption | `python scripts\check_session_resumable.py --project <project-dir>` | Surface in-flight tasks and blocked gates after interruption |
| Check computation checkpoints | `python scripts\check_computation_resumable.py --project <project-dir>` | Find orphaned long-run checkpoints |
| Write stage checkpoint | `python scripts\write_stage_checkpoint.py --project <project-dir> --stage N` | Summarize a research stage compactly |
| Scaffold paper review | `python scripts\scaffold_paper_review.py --project <project-dir> --paper-id P1 --title "Title"` | Create paper review note and index entry |
| Process paper PDF | `python scripts\process_paper_for_review.py --project <project-dir> --paper-id P1 --title "Title" --pdf <pdf-path>` | Scaffold, extract text, and draft provisional notes |
| Check paper review | `python scripts\check_paper_review_quality.py <review-path>` | Block weak literature notes before they support novelty |

Installed skills:

| Skill | Purpose |
|---|---|
| `task-intake` | Classify task, role, and first professor question |
| `professor-interview` | Turn ambiguity into a research question and next step |
| `literature-review-planning` | Plan literature access, PDFs, novelty map, and reproduction targets |
| `model-specification` | Record physical system, equations, variables, assumptions, and regimes |
| `baseline-strategy` | Choose variation vs new model and the first verification target |
| `seed-design` | Convert the research seed into testable task packets |
| `graduate-student` | Spawned worker: writes and runs code for one bounded task (parallelizable); reports evidence and hypotheses |
| `code-reviewer` | Static review of a graduate student's code (no execution) |
| `scientific-validator` | Independent re-run + validation against fixed criteria |
| `cache-log-auditor` | Mechanical audit of cache, logs, and outputs |
| `workflow-manager` | Refresh workflow + lineage state; report gate status |
| `peer-review-professor` | Adversarial review of claims and evidence |
| `baseline-validation` | Validate toy model, known limit, reproduction, or conservation check |
| `numerical-validation` | Check stability, convergence, uncertainty, and sensitivity |
| `dimensional-analysis` | Check dimensions, units, and nondimensionalization |
| `claim-to-evidence` | Link claim wording to evidence and claim ceiling |
| `scientific-verification-before-claim` | Verify evidence before claim strengthening |
| `anomaly-debugging` | Classify surprising or failed results before patching |
| `research-plan-review` | Review plan completeness, assumptions, and validation gaps |
| `researcher-review-loop` | Ask for researcher review at decision checkpoints |
| `research-retrospective` | Record outcome, reusable checks, failures, and open questions |
| `meeting` | Convene Lead/peer-review meetings for contested or high-stakes steps |
| `sync-workflow` | Refresh live workflow artifacts from filesystem state |
| `existing-research-onboarding` | Retrofit the harness onto an existing project |
| `harness-evaluation` | Evaluate whether the harness itself is working |

Named Dynamic Workflows:

Self-contained multi-agent workflow scripts under `.claude/workflows/*.js` are invocable by name (session-independent) instead of resending a full script. Each begins with an `export const meta = { name, description, phases }` literal whose `name` matches the filename.

| Workflow | Purpose |
|---|---|
| `harness-legacy-scan` | Read-only audit of the harness for stale rules, duplication, global-context tax, over-broad skills, product overlap, and risky permissions; emits a classified KEEP/SHRINK/MOVE/SPLIT/CONVERT/DELETE report with an adversarial counter-review. Never modifies files. |

## How Discipline Is Enforced

Research Partner separates surface guidance from blocking enforcement.

| Layer | Examples | Effect |
|---|---|---|
| Surface guidance | Skills, prompts, reviewer questions, meetings | Makes assumptions, risks, and decisions visible |
| Runtime hooks | Cross-tier write hook, Bash code-write hook, peer-review invocation hook | Blocks unsafe tool use or invalid invocation in the live runtime |
| Deterministic checkers | Capability manifest, spawn contracts, finding lifecycle, lineage, contract sync | Fail locally and in CI when repository state drifts |
| CI | `harness-checks.yml` with `evaluate_harness.py --fail-on-partial` | Makes new failed or partial harness scenarios red on every PR |

The deterministic spine is documented in `docs/hooks_reference.md`: capability manifest, spawn contracts, finding lifecycle, contract sync with word budget, and CI. This section belongs in README for researchers and contributors; it is intentionally not copied into `AGENTS.md`, which remains a slim resident contract.

Maintainers working inside this source repo should follow `docs/harness/self_hosting_development.md` when live hooks over-gate harness source edits.

## Vision

Research Partner aims to make AI assistance scientifically legible. A good run should leave behind assumptions, evidence, validation, figures, claims, waivers, and unresolved questions in a form another researcher can inspect. The goal is not more automation; it is harder-to-fake scientific discipline.
