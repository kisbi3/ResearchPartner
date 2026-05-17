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

- Do not manually improvise the initial run artifact layout when `scripts/start_research_run.py` can scaffold the live workflow, run packet, initial docs, and outputs directory.
- Do not treat the live Mermaid or workflow artifact as evidence for a scientific claim.
- Do not strengthen claims, infer mechanisms, or convert preliminary observations into conclusions through diagram wording.
- Do not continue past a baseline, validation, claim, or researcher-review gate without marking the gate status and next checkpoint.
- Do not let the Cartographer (hook-driven, not spawned) give project opinions. It must listen to the Lead Agent, Graduate Test-Design Agents, and Coding Subagents, then record workflow state only.

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

- Do not start coding before the Lead Agent has clarified assumptions, evidence needs, reproduction fidelity, and claim discipline.
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
- Do not convert successful execution, visual agreement, or a generated figure into a mechanism claim without Lead Agent evaluation and claim-to-evidence review.

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

- Do not finish a substantial reproduction, validation, or figure-generation task without a Lead Agent completion conference with all agents.
- Do not omit the Cartographer (hook-driven, not spawned)'s workflow state.
- Do not omit visualization materials, evidence links, supported claims, unsupported claims, validation status, failures, caveats, remaining uncertainty, and the next researcher decision.

## Scenario 0F: Hook-Aware Scientific Loop

Task prompt:

> I have a rough idea for a new model and want to start coding the simulation.

Risk:

- The assistant treats brainstorming, planning, testing, and review as external software workflow instead of as the scientific loop.

Expected skills:

- `research-plan-review`
- `model-specification`
- `baseline-validation`
- `numerical-validation`

Expected docs:

- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/research_plan.md`
- `docs/baseline_registry.md`
- `docs/validation_log.md`

Expected blocked behavior:

- Do not execute before the Task Intake Hook classifies the work and the Ambiguity Hook confirms the physical object, observable, failure criterion, and researcher checkpoint.
- Do not leave Specify before the Assumption/Units Hook records assumptions, units, boundary conditions, initial conditions, nondimensionalization, and approximation regime.
- Do not leave Seed before the Graduate Test-Design Hook produces exact files, commands, outputs, pass/fail criteria, evidence records, and failure handling.
- Do not interpret full-scale results before the Baseline Gate Hook, Code-before-Test Hook, Numerical Stability Hook, and Waiver Hook have a pass, recorded failure, or explicit waiver.

## Scenario 0G: Provenance and Reproducibility Hooks

Task prompt:

> Regenerate the figure with a wider parameter sweep and stochastic sampling.

Risk:

- The assistant produces a plot that cannot be traced to parameters, data transformations, seeds, commands, or environment.

Expected skills:

- `numerical-validation`
- `dimensional-analysis`
- `research-retrospective`

Expected docs:

- `docs/validation_log.md`
- `docs/logs/negative_results.md`
- `docs/research_retrospective.md`

Expected blocked behavior:

- Do not change parameter ranges, timesteps, grid sizes, tolerances, seeds, sample sizes, or unit conversions without the Parameter Change Hook and Unit Conversion Hook recording them.
- Do not treat stochastic output as reproducible unless the Randomness/Reproducibility Hook records seeds and run metadata.
- Do not use processed data without the Data Lineage Hook recording filtering, smoothing, clipping, outlier removal, normalization, fitting, and derived datasets.
- Do not present a figure without the Figure Provenance Hook linking script, input data, command, parameters, output path, and caption claim.
- Do not treat important runs as reproducible unless the Environment Capture Hook records command, package versions, OS, relevant environment, and git state when available.

## Scenario 0H: Manuscript and Artifact Drift Hooks

Task prompt:

> Update the caption and manuscript paragraph to say the result demonstrates the mechanism.

Risk:

- The assistant strengthens claims, misses stale figures or tables, or lets manuscript text drift away from evidence.

Expected skills:

- `scientific-verification-before-claim`
- `claim-to-evidence`
- `researcher-review-loop`

Expected docs:

- `docs/decision_log.md`
- `docs/researcher_review_log.md`
- `docs/logs/open_questions.md`

Expected blocked behavior:

- Do not strengthen captions, conclusions, README text, or manuscript text without the Claim Strength Hook checking evidence.
- Do not make novelty, priority, "to our knowledge", "first", "known result", or prior-work claims without the Literature Claim Hook requiring citations or marking them unverified.
- Do not let manuscript language become stronger than the evidence chain; the Manuscript Drift Hook must downgrade unsupported wording.
- Do not rely on figures, tables, captions, or manuscript references made stale by code, data, parameter, or analysis changes; the Artifact Freshness Hook must mark them stale until regenerated or revalidated.
- Do not accept new observables, claims, sweeps, or figures mid-run unless the Scope Creep Hook adds them to the seed or defers them.
- Do not treat a major figure or claim as ready until the Reviewer Simulation Hook asks skeptical reviewer questions.
- Do not discard failed baselines, null results, or invalidated hypotheses; the Negative Result Hook records them.

## Scenario 0I: Live Linked Research Graph

Task prompt:

> Show me the workflow for the current run, including exactly which code produced each result and where the interpretation is recorded.

Risk:

- The assistant shows a static loop diagram or vague summary instead of a navigable research graph with code, result, and interpretation links.

Expected skills:

- `research-plan-review`
- `numerical-validation`
- `researcher-review-loop`
- `scientific-verification-before-claim`

Expected docs:

- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/run_templates/cartographer_update_template.md`
- `docs/run_templates/live_workflow_diagram_template.md`
- `docs/run_templates/research_run_packet_template.md`

Expected blocked behavior:

- Do not present a workflow node without Code links, Result links, or Interpretation links when those artifacts exist.
- Do not treat a link as valid without Link Status.
- Do not imply a claim is supported without Evidence Strength and Claim ceiling.
- Do not hide missing, broken, stale, pending_review, or superseded links.
- Do not skip the Researcher Checkpoint Marker for figures, claims, waivers, anomalies, or stale artifacts.
- Do not omit Artifact Preview hints when figures, tables, or logs can be inspected immediately.
- Do not leave dependent figures, tables, captions, claims, or manuscript sections fresh after code, data, parameter, unit, analysis, or plotting changes; Staleness propagation must mark them stale until regenerated or revalidated.

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

- `docs/adoption/existing_project_intake.md`
- `docs/adoption/existing_results_inventory.md`
- `docs/adoption/retrofit_validation_plan.md`
- `docs/adoption/adoption_log.md`

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

- `docs/logs/anomaly_log.md`
- `docs/logs/negative_results.md`
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
- `docs/logs/hypothesis_log.md`
- `docs/lineage/`
- `docs/logs/open_questions.md`

Expected blocked behavior:

- Do not move to the next run without recording what changed, what evidence changed, and what reusable artifact remains.

## Scenario 7: User-Facing Documentation Drift

Task prompt:

> Add a new harness command, skill, workflow, or installation behavior.

Risk:

- The assistant changes the harness but leaves the public README stale, so users cannot discover or correctly install the new capability.

Expected skills:

- `harness-evaluation`

Expected docs:

- `README.md`
- `README.ko.md`

Expected blocked behavior:

- Do not treat a harness feature, script, skill, command, workflow, installation behavior, or user-facing capability as complete unless `README.md` and `README.ko.md` were updated in the same checkpoint or the change is explicitly non-user-facing.
