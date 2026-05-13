# Docs Shallow Structure Design

## Scope

Organize `docs/` so the research harness is easier to scan without breaking the high-traffic workflow paths that existing instructions, scripts, and tests use.

## Goal

Keep active research-control documents at `docs/` root and move supporting document families into shallow subfolders with a root index.

## Structure

Keep these root-level documents because they are common checkpoints or generated dashboards:

- `docs/research_plan.md`
- `docs/research_state.md`
- `docs/assumptions.md`
- `docs/baseline_registry.md`
- `docs/validation_log.md`
- `docs/decision_log.md`
- `docs/researcher_review_log.md`
- `docs/research_retrospective.md`
- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/workflow_code_map.md`
- `docs/workflow_map.json`
- `docs/workflow_map.html`
- `docs/paper_logic_diagram.md`

Move support documents into these folders:

- `docs/adoption/`: existing-project intake, artifact inventory, adoption log, retrofit validation plan.
- `docs/harness/`: harness evaluation plan, scenarios, log, and pilot protocol.
- `docs/logs/`: anomaly, hypothesis, negative-result, open-question, reproduction, tacit-pattern, and toy-model logs.

Preserve existing specialized folders:

- `docs/lineage/`
- `docs/run_templates/`
- `docs/superpowers/`

## Reference Updates

Update all direct references in root instructions, README, scripts, tests, and workflow documents so moved files remain discoverable.

## Validation

Run the existing harness and workflow-map tests after the move:

```powershell
python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py -q
```

Run static harness evaluation and workflow-link validation:

```powershell
python scripts/evaluate_harness.py
python scripts/validate_workflow_links.py
```
