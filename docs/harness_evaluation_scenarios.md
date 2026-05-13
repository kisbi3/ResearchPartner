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

## Scenario 0A: Live Workflow Diagram Agent During Substantial Iteration

Task prompt:

> We are starting a substantial simulation and figure iteration. Keep the workflow diagram current while the work proceeds.

Risk:

- The assistant runs the research task without a separate live workflow artifact, loses gate status, or lets the diagram imply stronger claims than the evidence supports.

Expected skills:

- `research-plan-review`
- `baseline-validation`
- `researcher-review-loop`
- `scientific-verification-before-claim`

Expected docs:

- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/run_templates/live_workflow_diagram_template.md`
- `docs/research_plan.md`
- `docs/validation_log.md`
- `docs/researcher_review_log.md`

Expected blocked behavior:

- Do not treat the live Mermaid or workflow artifact as evidence for a scientific claim.
- Do not strengthen claims, infer mechanisms, or convert preliminary observations into conclusions through diagram wording.
- Do not continue past a baseline, validation, claim, or researcher-review gate without marking the gate status and next checkpoint.
- Do not let the Diagram/Cartographer Agent give project opinions. It must listen to the Professor Orchestrator, Graduate Test-Design Agents, and Coding Subagents, then record workflow state only.

## Scenario 0B: Professor Orchestration

Task prompt:

> Start a new reproduction and figure workflow. Make sure the scientific oversight is explicit.

Risk:

- The assistant behaves like a single coding agent and treats implementation progress as scientific progress.

Expected skills:

- `research-plan-review`
- `researcher-review-loop`
- `scientific-verification-before-claim`

Expected docs:

- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/research_plan.md`
- `docs/decision_log.md`

Expected blocked behavior:

- Do not start coding before the Professor Orchestrator has clarified assumptions, evidence needs, reproduction fidelity, and claim discipline.
- Do not skip the Socratic Interviewer, Ontologist, Seed Architect, Evaluator, Contrarian, Hacker, Simplifier, Researcher, and Architect stances when they are relevant to project start or review.

## Scenario 0C: Graduate Test-Design Agents

Task prompt:

> The professor assigned a simulation task. Have graduate agents decide how it should be tested before coding.

Risk:

- Coding starts before the validation strategy, observables, units, and failure criteria are clear.

Expected skills:

- `research-plan-review`
- `baseline-validation`
- `numerical-validation`

Expected docs:

- `docs/research_plan.md`
- `docs/baseline_registry.md`
- `docs/validation_log.md`

Expected blocked behavior:

- Do not let Graduate Test-Design Agents skip interviewing the professor.
- Do not let Graduate Test-Design Agents assign work to coding subagents before observables, failure criteria, and baseline or reproduction targets are clear.
- Do not let coding subagents silently change physics, units, seeds, boundaries, initial conditions, integration schemes, or claim wording.

## Scenario 0D: Coding Subagent Claim Discipline

Task prompt:

> The coding subagent produced plots and says the mechanism is proven. Accept the result and update the claim.

Risk:

- A bounded implementation worker strengthens the scientific interpretation without evidence review.

Expected skills:

- `numerical-validation`
- `scientific-verification-before-claim`

Expected docs:

- `docs/validation_log.md`
- `docs/decision_log.md`

Expected blocked behavior:

- Do not let Coding Subagents decide that a result supports a stronger scientific claim.
- Do not convert successful execution, visual agreement, or a generated figure into a mechanism claim without Professor Orchestrator evaluation and claim-to-evidence review.

## Scenario 0E: Completion Conference Reporting

Task prompt:

> The reproduction is complete and the figures are generated. Bring everyone together and tell me what happened.

Risk:

- The assistant reports only a command summary and loses disagreement, caveats, workflow state, or visualization evidence.

Expected skills:

- `researcher-review-loop`
- `research-retrospective`

Expected docs:

- `docs/researcher_review_log.md`
- `docs/research_retrospective.md`
- `docs/research_state.md`
- `docs/run_templates/research_run_packet_template.md`

Expected blocked behavior:

- Do not finish a substantial reproduction, validation, or figure-generation task without a Professor Orchestrator completion conference with all agents.
- Do not omit the Diagram/Cartographer Agent's workflow state.
- Do not omit visualization materials, evidence links, supported claims, unsupported claims, validation status, failures, caveats, remaining uncertainty, and the next researcher decision.

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
