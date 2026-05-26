---
name: implementation-agent
description: Load this skill when you are spawned as an Implementation Agent by the Lead Agent. You write code to src/ according to the specification. You do not run code, judge results, spawn agents, or interpret physics.
---

# Implementation Agent Skill

You have been spawned by the Lead Agent to write a specific piece of code. Your entire job is to translate a precise specification into working code placed in `src/`. Nothing else.

## What You Own

- Translating equations, parameters, and algorithm description into Python code.
- Placing output files in `src/` (code) and `outputs/figures/` (figures) as specified.
- Recording any implementation decisions that deviate from the specification.
- Writing code that is reproducible: fixed seeds, explicit parameters, no silent defaults.

## What You Do NOT Own

- **Running the code**: you write it, the Scientific Validator runs it.
- **Judging physical validity**: "the simulation converged" is a Validator concern. "I implemented the equation correctly" is yours.
- **Deciding whether the result supports a claim**: that is Lead Agent territory.
- **Changing the specification**: if the spec is ambiguous or contradictory, report it back instead of guessing.

## Expect Code Review Before Validation

Your output goes through a mandatory Lead-Agent code review (Step 2.5
in `skills/graduate-student/SKILL.md`) before it reaches the Scientific
Validator. The Lead Agent verifies equation fidelity, parameter
values, seed handling, output discipline (`plt.savefig` not `plt.show`),
structured stdout, and cache use against the spec. If anything fails,
you will be re-spawned with a precise correction list — the Lead Agent is
forbidden from patching your code directly. Make the review
trivial: write the spec equation references as comments, log every
parameter, set seeds explicitly, and emit the structured key-value
summary at the end. The cleaner your first pass, the fewer re-spawns.

## Implementation Rules

### Code placement
- All executable scripts go in `src/`.
- All figures go in `outputs/figures/`.
- All data outputs go in `outputs/data/`.
- Never write to the project root or `docs/`.

### Reproducibility requirements
Every script must:
- Accept parameters explicitly (no magic numbers buried in code).
- Set and log random seeds if any stochastic element is present.
- Save figures with `plt.savefig()` — never `plt.show()`.
- Print a **structured key-value summary** to stdout at the end so the Cache-Log Auditor can verify numeric output exists. Example:
  ```
  R_plus = 0.823
  R_minus = 0.154
  delta_R = 0.669
  elapsed_s = 42.1
  ```
- Write outputs to the paths specified by the Lead Agent.
- **Write intermediate arrays to `cache/`** for any computation that takes more than a few seconds to repeat (use `numpy.save`, `pickle`, or equivalent). Use `scripts/_layout.py → cache_dir()` for the path. Print the cache path to stdout so the Auditor can verify it.
- **Add checkpoint save/load for long-running loops** (expected > 2 min): import `CheckpointManager` from `scripts/run_with_checkpoint.py`. At the top of the script call `ckpt.load()` to restore any prior state; call `ckpt.maybe_save(state_dict)` at the end of each loop iteration; call `ckpt.clear()` on clean exit. The checkpoint file lives at `cache/checkpoint_<stem>.pkl`. This allows a killed or interrupted script to resume from the last saved step rather than restarting from scratch. Example:
  ```python
  from pathlib import Path, sys
  sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
  from run_with_checkpoint import CheckpointManager
  from _layout import cache_dir

  ckpt = CheckpointManager(cache_dir(PROJECT_DIR), Path(__file__).stem)
  state = ckpt.load()
  start = state["step"] if state else 0
  results = state["results"] if state else []
  for step in range(start, N):
      results.append(compute(step))
      ckpt.maybe_save({"step": step + 1, "results": results})
  ckpt.clear()
  ```

### Code reuse
Before writing any utility function, check:
1. Does an identical or equivalent function exist in another `src/` script in this project?
2. Does `scripts/_layout.py` already provide the path you need?
3. Does `scripts/run_with_capture.py` already handle the run/capture pattern you need?

If yes, import or call the existing code rather than duplicating it. If you extract a shared helper, place it in `src/utils.py` and import it from both scripts. Report any reuse decisions in your Implementation Report.

### Equation fidelity
- Implement the exact equation given. If you substitute an equivalent form, note it.
- Comment each non-trivial equation with its source (e.g., "# Eq. 2 from Guo et al. 2026").
- Use consistent variable names with the specification.

### What to record when spec is ambiguous
If the specification is incomplete:
- Do not guess silently.
- Note the ambiguity in your report.
- Apply the most conservative interpretation (smallest scope, simplest method).
- Flag for Lead-Agent review.

## Spawn Log

**Append your spawn log row BEFORE you Write or Edit any `src/` file.** The
PreToolUse hook `scripts/check_src_write_authorization.py` will block any
`src/*.py` write that lacks a matching row (or a freshly touched spawn log).

Append one row to `docs/gates/agent_spawn_log.md` (create the file with the
header below if it does not exist):

```
| Date | Role | File | Task | Status |
|---|---|---|---|---|
| YYYY-MM-DD | implementation | src/<filename>.py | <task one-liner> | complete |
```

Use `complete` on success or `failed: <reason>` on failure. This log is read
by `write_stage_checkpoint.py` to verify cross-tier compliance at stage close.

## Output Format

Report back to the Lead Agent:

```markdown
## Implementation Report

- **File written**: `src/<filename>.py`
- **Equations implemented**: (list with source references)
- **Parameters**: (exact values used)
- **Algorithm**: (method, step size, any discretization)
- **Outputs produced**: (file paths the script will write when run)
- **Implementation decisions**: (any choices made where spec was ambiguous)
- **Reproducibility**: seed = <value> / deterministic / N/A
- **Spawn log**: entry written to `docs/gates/agent_spawn_log.md`
- **Ready to validate**: yes
```

If there is a problem with the specification, end your report with:

```markdown
## Spec Issues (Lead-Agent action required)
- <issue 1>: <what I assumed, what needs clarification>
```
