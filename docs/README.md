# Research Harness Docs

This directory keeps the research workflow visible: assumptions, validation state, workflow maps, researcher decisions, and lower-frequency support logs.

## Root Checkpoints

Use these files during ordinary research iterations:

- `research_plan.md`: active plan, assumptions, observables, validation gates, and review checkpoint.
- `research_state.md`: compact current state for resuming work.
- `assumptions.md`: assumptions that affect model meaning or interpretation.
- `baseline_registry.md`: baseline targets and validation status.
- `validation_log.md`: validation checks and evidence links.
- `decision_log.md`: researcher decisions that affect scope, model, validation, or claims.
- `researcher_review_log.md`: review packets and researcher feedback.
- `research_retrospective.md`: end-of-iteration outcome and lessons.

## Workflow Maps

- `workflow_overview.md`: human-readable workflow guide.
- `workflow_diagrams.md`: Mermaid workflow diagrams.
- `workflow_code_map.md`: map from skills and scripts to docs.
- `workflow_map.json`: source data for the interactive map.
- `workflow_map.html`: generated central copy of the interactive dashboard; `scripts/generate_workflow_map.py` also writes the latest run-local dashboard to `ResearchPartner-runs/.../workflow_map.html`.
- `paper_logic_diagram.md`: manuscript logic map, used only when paper planning starts.

## Subfolders

- `adoption/`: existing-project intake, artifact inventory, adoption log, and retrofit validation plan.
- `harness/`: harness evaluation plan, scenarios, log, and pilot protocol.
- `logs/`: anomaly, hypothesis, negative-result, open-question, reproduction, tacit-pattern, and toy-model logs.
- `lineage/`: reusable iteration lineage templates.
- `run_templates/`: templates for live workflow diagrams and full research run packets.
- `superpowers/`: design specs and implementation plans created by the agentic workflow.

## Rule of Thumb

If a document is needed at nearly every research gate, keep it at the root. If it supports a specific mode of work, put it in the matching subfolder and update references.
