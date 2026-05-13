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
