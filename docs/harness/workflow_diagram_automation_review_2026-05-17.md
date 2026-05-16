# Workflow Diagram Automation Review - 2026-05-17

## Scope

Reviewed whether the workflow diagram behavior works as intended:

1. A workflow diagram is created immediately when a research run starts.
2. The live workflow can keep being updated when agents request or emit updates.
3. The central workflow map reflects those updates.
4. Existing validation catches regressions in this behavior.

## Result

Status: **partial**

The run-local live workflow artifact is created at run start, and the Cartographer skill/template define recurring update packets. However, the central workflow map generator still looks for the old live workflow path, so newly scaffolded runs that use the current `docs/process/` layout can be ignored by `docs/workflow_map.html`.

## Evidence

### Start-of-run creation

`scripts/start_research_run.py` copies the live workflow template during run creation:

- `docs/process/live_workflow_diagram.md`
- `docs/process/cartographer_update_template.md`

An actual temporary run was created with:

```powershell
python scripts/start_research_run.py --name workflow-diagram-audit --date 2026-05-17 --runs-root C:\tmp\ResearchPartner-workflow-audit
```

Observed files:

- `docs/process/live_workflow_diagram.md`: exists
- `docs/process/cartographer_update_template.md`: exists
- `docs/gates/orient_note.md`: exists
- `research_run_packet.md`: exists
- `README.md`: exists
- `docs/live_workflow_diagram.md`: missing, which is expected for the current `docs/process/` layout

The generated `live_workflow_diagram.md` includes `Cartographer Update Events` and `Evidence Links` sections.

### Repeated agent updates

`skills/cartographer-update/SKILL.md` says to use the skill whenever live workflow state changes, including:

- active step changes
- gate pass/block events
- evidence links added, confirmed, broken, or stale
- waivers
- staleness propagation
- researcher checkpoints

The run template includes a `Cartographer Update Events` section with JSON packet structure. This is enough to support repeated agent-requested updates as a process convention.

### Central map integration gap

`scripts/generate_workflow_map.py` currently searches for:

```text
ResearchPartner-runs/*/docs/live_workflow_diagram.md
```

The current scaffolder creates:

```text
ResearchPartner-runs/*/docs/process/live_workflow_diagram.md
```

Observed current run roots:

- old-path live workflow files: 2
- new `docs/process/` live workflow files: 1
- newest `docs/process/` live workflow would be ignored by the current generator

This means `docs/workflow_map.html` can show an older run even after a newer research run has a valid live workflow artifact.

### Documentation drift

`docs/workflow_overview.md` still says the run scaffolder creates:

```text
docs/live_workflow_diagram.md
```

but current runs use:

```text
docs/process/live_workflow_diagram.md
```

`docs/run_templates/run_readme_template.md` correctly documents `docs/process/`.

### Validation coverage

Focused tests passed:

```powershell
python -m pytest tests/test_start_research_run.py tests/test_generate_workflow_map.py -q -p no:cacheprovider --basetemp C:/tmp/ResearchPartner-pytest-workflow-audit
```

Result:

```text
8 passed
```

But the tests do not cover the integration contract:

- `tests/test_start_research_run.py` correctly expects `docs/process/live_workflow_diagram.md`.
- `tests/test_generate_workflow_map.py` still creates fixtures at `docs/live_workflow_diagram.md`.

The general harness evaluator also passed most workflow-related scenarios:

```text
Scenarios: 22
Pass: 21
Partial: 1
Fail: 0
pre_run_workflow_navigation: partial
```

This does not catch the current path mismatch. `scripts/validate_workflow_links.py` also passes, but it validates static links rather than proving that the newest run-local workflow artifact feeds the central map.

## Gaps

1. **Central map generator path drift**
   - `generate_workflow_map.py` should read `docs/process/live_workflow_diagram.md`, probably with fallback support for legacy `docs/live_workflow_diagram.md`.

2. **Placeholder text is stale**
   - The no-active-run message still points researchers to `ResearchPartner-runs/*/docs/live_workflow_diagram.md`.

3. **Workflow overview path is stale**
   - `docs/workflow_overview.md` should say `docs/process/live_workflow_diagram.md`.

4. **Tests do not cover the current end-to-end path**
   - Add or update a generator test that creates a run using the current `docs/process/` layout and verifies that `live_workflow_map()` or the generated HTML uses it.

5. **No true periodic automation**
   - The harness defines event-driven updates through the Cartographer skill. It does not currently include a scheduler or daemon that periodically regenerates `docs/workflow_map.html`.
   - The current reliable model is: agents append/update the run-local live workflow artifact, then `python scripts/generate_workflow_map.py` regenerates the central HTML.

## Recommended Minimal Fix

1. Update `scripts/generate_workflow_map.py` to search both:
   - `*/docs/process/live_workflow_diagram.md`
   - `*/docs/live_workflow_diagram.md`

2. Prefer the newest file by modification time across both paths.

3. Update stale path text in:
   - `scripts/generate_workflow_map.py`
   - `docs/workflow_overview.md`

4. Update `tests/test_generate_workflow_map.py` so at least one fixture uses `docs/process/live_workflow_diagram.md`.

5. Add a harness evaluation scenario that checks the integration from `start_research_run.py` to `generate_workflow_map.py`.

## Bottom Line

The live workflow process is present, but not fully closed-loop. Research start creates the run-local diagram, and agents have a defined update route. The weak point is central visualization freshness: `workflow_map.html` can miss the latest run because generator discovery still uses the old path.

## Resolution - 2026-05-17

Status: **resolved**

Implemented the minimal fix:

- `scripts/generate_workflow_map.py` now searches both current and legacy live workflow paths:
  - `ResearchPartner-runs/*/docs/process/live_workflow_diagram.md`
  - `ResearchPartner-runs/*/docs/live_workflow_diagram.md`
- The newest live workflow artifact is selected by modification time across both layouts.
- The no-active-run placeholder text now points to `docs/process/live_workflow_diagram.md`.
- `docs/workflow_overview.md` now documents the current `docs/process/` layout and legacy fallback.
- `README.md` and `README.ko.md` now document the run-local live workflow path and the need to rerun `generate_workflow_map.py` after Cartographer updates.
- `tests/test_generate_workflow_map.py` now covers the current scaffold layout and newest-file selection across current and legacy layouts.
- `scripts/evaluate_harness.py` now includes `live_workflow_map_scaffold_integration` so this integration surface is represented in harness evaluation.

Verification commands:

```powershell
python -m pytest tests/test_generate_workflow_map.py::test_latest_live_workflow_path_reads_current_scaffold_layout tests/test_generate_workflow_map.py::test_latest_live_workflow_path_prefers_newest_current_or_legacy_layout -q -p no:cacheprovider --basetemp C:/tmp/ResearchPartner-pytest-workflow-red2
python -m pytest tests/test_start_research_run.py tests/test_generate_workflow_map.py -q -p no:cacheprovider --basetemp C:/tmp/ResearchPartner-pytest-workflow-green
python scripts/evaluate_harness.py
python scripts/validate_workflow_links.py
```
