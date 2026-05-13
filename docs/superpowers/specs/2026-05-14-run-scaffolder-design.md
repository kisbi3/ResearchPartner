# Run Scaffolder Design

## Scope

Add a small command-line scaffolder that starts a research run from the existing run templates.

The task classification is:

- Workflow visualization
- Reproducibility check
- Harness evaluation
- Code maintenance

## Goal

Starting a substantial research run should produce the same basic artifact layout every time, without the researcher manually copying templates. The scaffolder should create a run directory, copy the live workflow and research run packet templates, and add the minimal docs/logs expected by the live workflow map.

## Command

```bash
python scripts/start_research_run.py --name 1d-diffusion-mode-decay
```

The command creates:

```text
ResearchPartner-runs/YYYY-MM-DD-1d-diffusion-mode-decay/
  docs/
    live_workflow_diagram.md
    research_plan.md
    baseline_registry.md
    validation_log.md
    researcher_review_log.md
    research_retrospective.md
  outputs/
  research_run_packet.md
```

By default, `ResearchPartner-runs` is a sibling of the harness root. Tests can override it with `--runs-root`.

## Behavior

- Slugify the run name into a filesystem-safe lowercase slug.
- Refuse to overwrite an existing run directory.
- Copy `docs/run_templates/live_workflow_diagram_template.md` to `docs/live_workflow_diagram.md`.
- Copy `docs/run_templates/research_run_packet_template.md` to `research_run_packet.md`.
- Create minimal placeholder docs for plan, baseline, validation, researcher review, and retrospective logs.
- Print the created run path.

## Non-Goals

- Do not validate whether the run packet is complete.
- Do not infer physical assumptions.
- Do not generate figures.
- Do not update scientific claims.
- Do not create autonomous runtime agents.

## Validation Plan

- Add tests for run creation, template copying, expected docs, and duplicate protection.
- Run the scaffolder tests.
- Run existing evaluator and workflow-map tests.
- Run the harness evaluator.
- Confirm no executable code or notebook uses `plt.show()`.
