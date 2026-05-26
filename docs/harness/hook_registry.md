# Hook Registry

The machine-readable source of truth is `docs/harness/capability_manifest.json`.
This file is the readable map for maintainers.

Run after changing any hook, checker, workflow gate key, skill contract, or profile:

```powershell
python scripts/check_harness_manifest.py --project <project-dir>
python scripts/check_spawn_contracts.py --project <project-dir>
```

## Current Wired Hooks

| Phase | Matcher | Registry ids |
|---|---|---|
| PreToolUse | `Agent` | `agent-gate-sequence`, `agent-workflow-pre`, `peer-review-invocation` |
| PreToolUse | `Write\|Edit` | `write-authorization`, `write-path-pre`, `write-workflow-pre` |
| PreToolUse | `Bash\|PowerShell` | `bash-code-write`, `seed-before-full-run`, `orphan-checkpoints-warning` |
| PostToolUse | `Agent` | `agent-workflow-post`, `agent-spawn-log-integrity` |
| PostToolUse | `Write\|Edit` | `write-workflow-post`, `write-path-post` |
| PostToolUse | `Bash\|PowerShell` | `bash-workflow-post`, `bash-path-post` |

## Rules

- Hook commands must use `python "$CLAUDE_PROJECT_DIR/scripts/<script>.py"` rather than `python scripts/<script>.py`.
- Every wired hook script in `.claude/settings.local.json` must appear in `hook_registry` or in `known_uncovered_wired_hooks`.
- `known_uncovered_wired_hooks` is a temporary migration escape hatch and should be empty before release.
- Workflow references use real generator keys such as `interview_gate`, not guessed rendered node ids such as `gate_interview`.
- Spawn role changes must pass `check_spawn_contracts.py`: required `.claude/agents/<role>.md` files, `tools:` frontmatter, `subagent_type` names, Graduate Student child roles, and explicit-spawn-only descriptions must match `docs/harness/spawn_contracts.json`.
