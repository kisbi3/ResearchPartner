# Retrofit Validation Plan

| ID | Target Artifact | Validation Needed | Minimal Check | Owner | Priority | Status |
|---|---|---|---|---|---|---|
| RV-001 |  |  |  |  | low/medium/high | planned/running/pass/fail/partial/waived |

## Planning Rules

When adopting the harness into an existing project:

1. Start with the smallest target that can change interpretation.
2. Prefer reproducing an existing figure or validating a toy/known-limit case.
3. Mark unknowns honestly.
4. Do not block all work on a complete audit unless the researcher requests it.
5. Record waived checks and their risk.

## Common Retrofit Checks

- dimensional check for a core equation
- rerun one existing figure from source
- compare one solver result to an analytical limit
- conservation-law check for one simulation
- claim-to-evidence map for one manuscript section
- parameter and seed recovery for one prior run
