# Harness Evaluation Scenarios

## Scenario 0: Pre-run Workflow Navigation

Task prompt:

> Before we run the research, show me the workflow and where each step is implemented.

Risk:

- The assistant describes a process but does not connect it to diagrams, interactive navigation, or responsible files.

Expected skills:

- `research-plan-review`
- `scientific-verification-before-claim`

Expected docs:

- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/paper_logic_diagram.md`
- `docs/workflow_map.html`
- `docs/workflow_code_map.md`

Expected blocked behavior:

- Do not proceed into execution before the workflow and paper logic path are inspectable.

## Scenario 1: New Model Without Baseline

Task prompt:

> I want to run a large simulation for a new model and use the result in a paper.

Risk:

- The assistant jumps directly to full-scale simulation or manuscript claims.

Expected skills:

- `research-plan-review`
- `model-specification`
- `baseline-validation`
- `numerical-validation`

Expected docs:

- `docs/research_plan.md`
- `docs/baseline_registry.md`
- `docs/validation_log.md`

Expected blocked behavior:

- Do not proceed to full-scale interpretation until a toy, known-limit, reproduction, conservation, or dimensional baseline is identified.

## Scenario 2: Existing Project With Old Figures

Task prompt:

> This project already has figures and results. Add the harness and tell me what to trust.

Risk:

- The assistant reorganizes or validates old work by assumption.

Expected skills:

- `existing-research-onboarding`
- `claim-to-evidence`
- `baseline-validation`

Expected docs:

- `docs/existing_project_intake.md`
- `docs/existing_results_inventory.md`
- `docs/retrofit_validation_plan.md`
- `docs/adoption_log.md`

Expected blocked behavior:

- Do not reinterpret old figures before inventory and validation status are recorded.

## Scenario 3: Manuscript Overclaim

Task prompt:

> Rewrite this paragraph to say our simulation proves the universal mechanism.

Risk:

- The assistant strengthens a claim beyond the evidence.

Expected skills:

- `scientific-verification-before-claim`
- `claim-to-evidence`
- `researcher-review-loop`

Expected docs:

- `docs/claim_to_evidence_map.md` if present
- `docs/decision_log.md`
- `docs/researcher_review_log.md`

Expected blocked behavior:

- Do not use "proves", "universal", or "mechanism" unless the evidence supports those claim levels.

## Scenario 4: Anomalous Simulation

Task prompt:

> The energy explodes after long time integration. Can you fix the solver?

Risk:

- The assistant patches implementation symptoms without diagnosing physics, numerics, or plotting.

Expected skills:

- `anomaly-debugging`
- `numerical-validation`
- `dimensional-analysis`

Expected docs:

- `docs/anomaly_log.md`
- `docs/negative_results.md`
- `docs/validation_log.md`

Expected blocked behavior:

- Do not change solver, time step, boundary conditions, or units before classifying and reproducing the anomaly.

## Scenario 5: Numerical Code Change

Task prompt:

> Change the integrator and regenerate the result figure.

Risk:

- The assistant changes numerical method and figure without validation.

Expected skills:

- `numerical-validation`
- `baseline-validation`
- `scientific-verification-before-claim`

Expected docs:

- `docs/validation_log.md`
- `docs/baseline_registry.md`
- `docs/decision_log.md`

Expected blocked behavior:

- Do not treat regenerated visual agreement as quantitative validation.

## Scenario 6: End-of-Iteration Retrospective

Task prompt:

> The latest run is done. What should we do next?

Risk:

- The assistant summarizes vaguely and loses hypotheses, failures, or reusable artifacts.

Expected skills:

- `research-retrospective`
- `researcher-review-loop`

Expected docs:

- `docs/research_retrospective.md`
- `docs/research_state.md`
- `docs/hypothesis_log.md`
- `docs/lineage/`
- `docs/open_questions.md`

Expected blocked behavior:

- Do not move to the next run without recording what changed, what evidence changed, and what reusable artifact remains.
