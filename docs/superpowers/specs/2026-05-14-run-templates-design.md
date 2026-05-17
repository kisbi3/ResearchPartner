# Run Templates Design

> **Historical design doc.** This describes the original 3-tier Professor-Orchestrator design from 2026-05-14. The current implementation absorbs that role into the **Lead Agent** (main conversation context); see [docs/orchestration_protocol.md](../../orchestration_protocol.md) for the current 2-tier spawn hierarchy. Terminology in this file is kept as written to preserve design history.


## Scope

This design adds lightweight run-level templates for the professor-led orchestration protocol. It avoids a large template family and keeps only the artifacts that should be reused during real research runs.

The task classification is:

- Workflow visualization
- Researcher review
- Research retrospective
- Harness evaluation
- Code maintenance

## Goal

Every substantial research run should have a small, reusable packet that records how the agents clarified, executed, evaluated, visualized, and reported the work. The packet should support the Professor Orchestrator, Graduate Test-Design Agents, Coding Subagents, and Diagram/Cartographer Agent without turning the process into paperwork.

## Minimal Template Set

Create two templates under `docs/run_templates/`:

- `live_workflow_diagram_template.md`: the Diagram/Cartographer Agent's live Mermaid workflow artifact. It records process state only and does not give project opinions or scientific interpretations.
- `research_run_packet_template.md`: the main run packet. It includes Interview, Seed, Execute, Evaluate, Completion Conference, User Report, and Retrospective sections in one file.

Do not create separate interview-log or user-report templates in this pass. Those would duplicate the run packet and make the workflow heavier.

## Template Boundaries

The live workflow template is owned by the Diagram/Cartographer Agent. It should listen to the Professor Orchestrator, Graduate Test-Design Agents, and Coding Subagents, then record active steps, gates, evidence links, blocked behaviors, and review checkpoints.

The research run packet is owned by the Professor Orchestrator. Graduate agents provide test-design notes, coding subagents provide execution reports, and the Diagram/Cartographer Agent provides workflow state. The Professor Orchestrator uses those inputs to run the completion conference and prepare the user-facing report.

## Documentation and Evaluation

Update workflow documentation and harness evaluation so the templates are discoverable and checked. The evaluator should fail or degrade if substantial-work scenarios no longer point to the run templates.

## Validation Plan

- Confirm both templates exist.
- Confirm workflow docs and workflow code map reference the templates.
- Confirm the harness evaluator includes the templates in relevant scenarios.
- Run evaluator tests and workflow-map tests.
- Run the harness evaluator.
- Confirm no executable code or notebook uses `plt.show()`.
