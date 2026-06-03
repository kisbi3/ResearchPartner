# Self-Hosting Development Procedure

## Purpose

This repo is both the harness source and a marked research project. That creates self-hosting over-gating: the same hooks that correctly protect real research projects can make harness maintenance awkward when editing tests, scripts, or the resident contract files.

The goal is to keep real-project enforcement strong while giving maintainers a clear procedure for source-repo work.

## Rule

Do not add a permanent self-development bypass to the runtime contract. A broad bypass would weaken the same gates that installed projects depend on.

For harness source development, use this procedure instead:

1. Confirm the current branch and worktree state.
2. Move the source repo's `.research-harness` marker aside before editing files that the live hooks intentionally gate.
3. Make the harness source change.
4. Restore `.research-harness` before validation.
5. Run the deterministic checks before committing:

```text
python scripts/check_contract_sync.py
python scripts/check_harness_manifest.py
python scripts/check_spawn_contracts.py
python scripts/check_domain_manifest.py
python scripts/evaluate_harness.py --fail-on-partial
python -m pytest -q
```

## Boundaries

- This procedure is for the harness source repository only.
- Installed research projects should keep `.research-harness` in place.
- Do not use this procedure to bypass PI-owned gate decisions.
- Do not commit with `.research-harness` missing unless the change explicitly concerns source-repo self-use metadata.
