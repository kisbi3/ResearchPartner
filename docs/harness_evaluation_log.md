# Harness Evaluation Log

| ID | Date | Scope | Command / Method | Result | Main Gap | Next Evaluation |
|---|---|---|---|---|---|---|
| HE-001 | 2026-05-13 | Core scenario coverage | `python scripts/evaluate_harness.py` | 5 pass, 1 partial, 0 fail, average 98 | Anomaly scenario needed stronger top-level expected behavior wording | Re-run after rule update |
| HE-002 | 2026-05-13 | Core scenario coverage after rule update | `python scripts/evaluate_harness.py` | 6 pass, 0 partial, 0 fail, average 100 | Automated evaluation is static; needs live pilot | Run `docs/harness_pilot_protocol.md` on a real or mock research task |
| HE-003 | 2026-05-13 | Workflow navigation and paper logic coverage | `python scripts/evaluate_harness.py` | 7 pass, 0 partial, 0 fail, average 100 | Still needs live researcher pilot of `docs/workflow_map.html` | Run pilot before first real research campaign |

## Rules

Record every evaluation of the harness itself.

For each evaluation, include:

- scenario coverage
- failing or partial scenarios
- usability risks
- changes made because of the evaluation
- whether a researcher reviewed the evaluation
