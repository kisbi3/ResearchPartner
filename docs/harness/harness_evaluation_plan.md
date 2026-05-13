# Harness Evaluation Plan

## Purpose

Evaluate whether the physics research harness will actually shape research behavior, not just add documents.

## Evaluation Questions

1. Does a realistic task trigger the right skill?
2. Does the harness block premature claims?
3. Does it force baseline or reproduction work before full-scale interpretation?
4. Does it handle already-running research without rewriting history?
5. Does it preserve anomalies, negative results, and open questions?
6. Does each iteration leave a reusable artifact?
7. Can the researcher inspect the workflow and paper logic before execution?
8. Is the required workflow lightweight enough to be used?

## Evaluation Layers

| Layer | Question | Method |
|---|---|---|
| Structure | Are required files present? | `scripts/run_baseline_validation.py` |
| Scenario behavior | Do realistic tasks map to the right skills and logs? | `scripts/evaluate_harness.py` |
| Usability | Is the workflow too heavy or vague? | Researcher review of scenario results |
| Pilot | Does the harness help in an actual session? | `docs/harness/harness_pilot_protocol.md` |

## Pass Criteria

The harness is considered usable for trial adoption when:

- all structural checks pass
- all core scenarios are pass or partial
- no core scenario fails due to missing skill coverage
- no scenario requires more than one first action before giving the researcher a useful next step
- at least one pilot task has been run before relying on the harness for a real manuscript or major simulation campaign

## Re-evaluation Triggers

Run evaluation when:

- a new skill is added
- `AGENTS.md`, `GEMINI.md`, or `PHYSICS.md` changes
- the harness is copied into an existing research repo
- a researcher reports that the workflow was skipped, confusing, or too heavy
