# Harness Evaluation Log

| ID | Date | Scope | Command / Method | Result | Main Gap | Next Evaluation |
|---|---|---|---|---|---|---|
| HE-001 | 2026-05-13 | Core scenario coverage | `python scripts/evaluate_harness.py` | 5 pass, 1 partial, 0 fail, average 98 | Anomaly scenario needed stronger top-level expected behavior wording | Re-run after rule update |
| HE-002 | 2026-05-13 | Core scenario coverage after rule update | `python scripts/evaluate_harness.py` | 6 pass, 0 partial, 0 fail, average 100 | Automated evaluation is static; needs live pilot | Run `docs/harness/harness_pilot_protocol.md` on a real or mock research task |
| HE-003 | 2026-05-13 | Workflow navigation and paper logic coverage | `python scripts/evaluate_harness.py` | 7 pass, 0 partial, 0 fail, average 100 | Still needs live researcher pilot of `docs/workflow_map.html` | Run pilot before first real research campaign |
| HE-004 | 2026-05-13 | Live workflow pilot after 1D diffusion run | `python scripts/evaluate_harness.py`; `python -m pytest tests`; review of `ResearchPartner-runs/2026-05-13-1d-diffusion-mode-decay` artifacts | 8 pass, 0 partial, 0 fail, average 100; 5 tests passed | Strong structurally, but still relies on the agent regenerating `workflow_map.html` after live workflow updates; anomaly path has not been exercised with a real failed run | Run an intentional anomaly pilot and consider automating live workflow regeneration |
| HE-005 | 2026-05-13 | Strong-partner framing and intentional anomaly pilot | `python scripts/evaluate_harness.py`; `python -m pytest tests`; `python -m pytest ResearchPartner-runs/.../tests`; `python scripts/validate_workflow_links.py` | 8 pass, 0 partial, 0 fail, average 100; harness tests passed; run tests passed | Framing now explicitly rejects full automation, and the numerical-instability anomaly path was exercised; remaining gap is researcher review of whether the partner-style stop feels clear enough | Ask researcher to choose fixed-ratio convergence, multi-mode validation, or another anomaly class |
| HE-006 | 2026-05-14 | Docs shallow-structure reorganization | `python -m pytest tests/test_evaluate_harness.py tests/test_generate_workflow_map.py -q`; `python scripts/evaluate_harness.py`; `python scripts/validate_workflow_links.py`; `python scripts/run_baseline_validation.py` | 7 tests passed; 12 pass, 0 partial, 0 fail, average 100; workflow links passed; baseline harness check passed | Structural paths are updated, but tracked Python cache files can still change during validation | Decide whether generated `__pycache__` files should remain tracked |

## Rules

Record every evaluation of the harness itself.

For each evaluation, include:

- scenario coverage
- failing or partial scenarios
- usability risks
- changes made because of the evaluation
- whether a researcher reviewed the evaluation
