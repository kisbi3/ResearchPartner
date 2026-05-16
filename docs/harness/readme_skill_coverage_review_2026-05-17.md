# README Skill Coverage Review - 2026-05-17

## Scope

Reviewed whether `README.md` describes the current skill library under `skills/**/SKILL.md`.

## Evidence

- Actual skill files found: 24.
- `README.md` Installed Skills table rows found: 23.
- `README.ko.md` Installed Skills table rows found: 23.
- Extra README table entries that do not exist as skills: none.
- Missing from both README tables: `professor-interview`.

## Finding

`README.md` does not fully describe every current skill. The `professor-interview` skill exists at `skills/professor-interview/SKILL.md`, but it is absent from the README Installed Skills table.

The skill frontmatter describes it as:

> Use after task-intake to run a free-form brainstorming dialogue between the Professor Orchestrator and the researcher. The professor probes assumptions, challenges framing, and crystallizes the research question before Specify, Seed, or literature work begins. This is the Interview phase.

This omission matters because `task-intake` routes most substantive research tasks to `professor-interview` as the next skill, so the README skips a core Orient-to-Interview transition.

## Quality Notes

The remaining README skill rows are broadly aligned with the corresponding skill frontmatter. Some README descriptions are shorter than the skill files, but they are acceptable as quick-start descriptions because the README explicitly says the assistant should load skills on demand instead of treating the README as the full operating manual.

## Recommended Fix

Add `professor-interview` to the Installed Skills table in both `README.md` and `README.ko.md`.

Suggested English row:

```markdown
| `professor-interview` | After task-intake — Professor Orchestrator interviews the researcher to surface assumptions, challenge framing, and crystallize the research question before Specify, Seed, or literature work begins |
```

Suggested Korean row:

```markdown
| `professor-interview` | task-intake 이후 — Professor Orchestrator가 연구자와 인터뷰하여 가정과 프레이밍을 점검하고 Specify, Seed, 문헌 작업 전에 연구 질문을 구체화할 때 |
```
