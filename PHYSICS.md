# General Physics Research Rules

## Scientific Standard

A result should be interpreted according to the strongest support available:

1. Exact analytical derivation
2. Controlled approximation
3. Numerical solution with validation
4. Empirical data analysis with uncertainty
5. Qualitative analogy
6. Speculation

Do not present a lower-level result as if it had higher-level support.

## Evidence Before Claim

No scientific claim should be strengthened without fresh or recorded evidence.

Before using strong language, check whether the claim is supported by:

- exact derivation
- controlled approximation
- validated numerical result
- empirical data with uncertainty
- reproduced benchmark
- figure or table with clear provenance
- citation
- explicit assumption

Use the weakest language that the evidence supports.

## Equation Discipline

For every important equation, check:

- Definition of all variables
- Units and dimensions
- Domain of validity
- Assumptions
- Boundary conditions
- Initial conditions
- Limiting cases
- Sign conventions
- Coordinate system
- Whether variables are dimensional or nondimensional

## Dimensional Consistency

Every physically meaningful equation must be dimensionally consistent.

When dimensions do not match:

- Stop and report the inconsistency.
- Do not patch the equation by guessing.
- Identify which variable, constant, or scaling factor is missing.

## Approximation Discipline

When using approximations, state:

- Small or large parameter
- Expansion order
- Neglected terms
- Expected error scale
- Validity regime
- Breakdown regime

Examples:

- small-angle approximation
- weak-coupling approximation
- continuum limit
- thermodynamic limit
- mean-field approximation
- linear response
- low-temperature / high-temperature limit
- nonrelativistic / ultrarelativistic limit

## Numerical Simulation Discipline

For simulations, track:

- Governing equations
- Discretization
- Time step
- Spatial resolution
- Solver/integrator
- Boundary conditions
- Initial conditions
- Parameters
- Random seed
- Convergence checks
- Conservation checks
- Stability checks

A simulation result is not manuscript-ready unless its numerical reliability has been checked.

## Baseline-First Discipline

Before trusting a new model, solver, analysis pipeline, or figure workflow, validate it on at least one baseline:

- toy model with known behavior
- analytically solvable limit
- reproduced result from literature
- previous validated output
- conservation-law test
- dimensional sanity case

A full result should not be interpreted scientifically until the baseline status is recorded, unless the researcher explicitly waives this requirement.

## Iterative Researcher Review

Physics research should move in reviewable iterations:

1. Run or derive the smallest meaningful next result.
2. Separate raw result, interpretation, uncertainty, and speculation.
3. Present the result to the researcher with the exact assumptions and validation status.
4. Record the researcher's decision or requested change.
5. Use that decision to choose the next model, run, figure, or manuscript revision.

Do not let an automated workflow silently turn preliminary output into a scientific conclusion.

## Existing Research Retrofit Discipline

When attaching this harness to a project that already has results:

- Preserve the existing artifact layout until the inventory is complete.
- Treat previous figures, tables, manuscript claims, and numerical results as unvalidated unless their evidence is recorded.
- Do not silently convert units, nondimensionalization, boundary conditions, seeds, or plotting scripts to fit the harness.
- Build a map from existing artifacts to assumptions, models, scripts, data, validation status, and claims.
- Start with one narrow retrofit target before attempting a full project audit.
- Prefer reproducing one existing figure or toy result before changing the research direction.

The first retrofit goal is not to judge the whole project. It is to make the current scientific state visible enough that a researcher can decide what to validate next.

## Research Memory and Lineage

The research state should be recoverable from files, not from conversation history.

Maintain compact records of:

- current research state
- hypotheses and predictions
- open questions
- negative results
- anomalies
- tacit patterns
- iteration lineage

Each iteration should record the starting state, hypothesis or objective, prediction, method, result, validation status, researcher feedback, reflection, reusable artifact, and next action.

## Workflow Visibility

Before executing substantial research, the intended workflow should be visible to the researcher.

Use:

- workflow overview for the step-by-step process
- workflow diagrams for the research path
- interactive workflow map for navigation to responsible skills, docs, and scripts
- paper logic diagram when results may become a manuscript

The workflow map should connect each step to the code or document that owns the responsibility.

## Workflow Diagram Rules

The live workflow diagram (`docs/process/live_workflow_diagram.md` inside the project) must be kept current. Violations leave the researcher blind to run state.

**How workflow state is updated:**

- **Agent() spawns** are tracked automatically by `scripts/workflow_hooks.py` (pre/post hooks). No manual command needed — the In-Flight Tasks table and Real-Time Event Log are updated on every spawn.

- **Gate status and lineage** are updated by running `/sync-workflow`:
  ```
  python scripts/sync_workflow.py --project <project-dir>
  ```
  Run this after completing a gate step, finishing a stage, or after writing any artifact with a `lineage:` front-matter block.

- **Lineage edges** (e.g. `evolved_from`, `reproduces`, `cites_paper`, `supports`, `limits`) are declared in the artifact file itself as YAML front-matter:
  ```yaml
  ---
  lineage:
    node_type: result
    reproduces: paper_smith2020
  ---
  ```
  Then `/sync-workflow` picks up the front-matter and rebuilds the graph.

See `skills/sync-workflow/SKILL.md` for the full front-matter spec and node type reference.

## Compound Research Discipline

Every research iteration should make later iterations easier.

Prefer leaving behind:

- reusable baseline
- benchmark script
- validation command
- toy model
- reproduction recipe
- anomaly diagnosis
- claim-to-evidence map
- decision record
- tacit pattern
- improved skill rule

If an iteration leaves no reusable artifact, record why.

## Anomaly Discipline

When a result behaves unexpectedly, classify the anomaly before fixing it.

Possible classes include physical effect, model misspecification, invalid approximation, dimensional error, boundary or initial condition issue, numerical instability, convergence failure, implementation bug, data preprocessing error, plotting error, stochastic fluctuation, interpretation overreach, and unknown.

Before changing code, parameters, units, or interpretation, state the expected behavior, observed behavior, smallest reproduction, current classification, and next diagnostic.

## Conservation Laws

When applicable, check:

- Energy conservation
- Momentum conservation
- Angular momentum conservation
- Charge conservation
- Probability conservation
- Mass conservation
- Entropy production or monotonicity
- Symmetry constraints

If a conservation law is violated, determine whether the violation is physical, numerical, or due to model assumptions.

## Limiting Cases

Every model should be tested in simple limits when possible:

- zero coupling
- infinite coupling
- zero temperature
- high temperature
- noninteracting limit
- linear regime
- continuum limit
- large system limit
- small system limit
- equilibrium limit
- noiseless limit
- high-noise limit

## Error and Uncertainty

Report uncertainty using appropriate methods:

- analytical error estimate
- discretization error
- convergence error
- statistical uncertainty
- bootstrap / jackknife
- finite-size effects
- finite-time effects
- parameter sensitivity
- model misspecification
- measurement uncertainty

## Figure Interpretation

A figure can support:

- qualitative pattern
- quantitative estimate
- comparison
- scaling behavior
- failure of a model
- consistency with a theory

A figure alone does not prove a mechanism unless the mechanism is isolated by the model or experiment.

## Manuscript Claim Discipline

Use careful language:

Preferred:

- "is consistent with"
- "suggests"
- "within this model"
- "under these assumptions"
- "in the tested parameter regime"
- "numerically supports"
- "agrees with the analytical limit"

Avoid unless justified:

- "proves"
- "demonstrates conclusively"
- "reveals the mechanism"
- "establishes universality"
- "confirms causality"
