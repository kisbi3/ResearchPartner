---
name: baseline-strategy
description: Use after model-specification to decide whether the model is a variation of prior work (requiring reproduction) or a genuinely new model (requiring analytical limit verification). The professor and graduate student conduct a structured dialogue and must agree on one path before seed-design begins.
---

# Baseline Strategy Skill

Use this skill after model-specification completes and before seed-design begins.

## Goal

Establish the first verification target before any code is written or simulation is run. The professor and graduate student hold a focused dialogue and must agree on exactly one of two paths:

1. **Variation** — the model modifies or extends an existing published model. The first seed task must reproduce a specific, quantitative result from the parent model.
2. **New model** — the model is genuinely novel with no direct published ancestor. The first seed task must verify code against at least one analytically tractable limit or approximation (e.g., mean-field theory, zero-temperature limit, perturbation theory, dimensional analysis target).

The dialogue must not end until both parties agree on the path and the specific target. Vague answers ("it's similar to X", "the physics is well-known") are not acceptable — the professor must push until the target is quantitative and the pass criterion is explicit.

## Prerequisites

Confirm the Model Gate passes: `python scripts/check_model_specified.py --run <run-dir>`. If not, complete model-specification first.

## Dialogue Format

The professor reads `docs/model_spec.md` before opening the conversation. The professor then leads with probing questions; the graduate student must defend the classification.

**Opening questions for Variation path:**
- Which paper or validated code does this model derive from?
- What exactly was changed from the parent? (equation, parameter, geometry, boundary condition?)
- What is the key result to reproduce — a specific number, curve, or phase boundary?
- What numerical tolerance constitutes a successful reproduction?

**Opening questions for New model path:**
- What is the simplest analytically solvable limit of this model?
- What does mean-field theory (or another tractable approximation) predict?
- Can dimensional analysis constrain any output to within a factor?
- What is the expected result, and what tolerance defines "code is correct"?

The dialogue continues until the researcher confirms both the path and target are crystallized.

## Professor Stances

The professor uses stances fluidly:

- **Socratic Interviewer** — ask one question at a time, wait for a real answer
- **Contrarian** — challenge the classification ("are you sure this isn't a variation of Smith 2019?")
- **Hacker** — demand a quick back-of-envelope estimate ("what order of magnitude do you expect?")
- **Simplifier** — push for the single most important number ("what is the one quantity this must reproduce?")
- **Architect** — check whether the chosen target actually tests the part of the model that was changed

## Meeting Trigger

If the dialogue ends with a decision that was uncertain or contested — either party was not fully convinced — recommend a meeting before seed-design begins:

```
Recommend: meeting --scope quick --on "is the variation/new-model classification correct for <model name>?"
```

A misclassification at this stage sets Task 1 in the wrong direction: either spending time reproducing a parent result for a model that is not actually a variation, or skipping a reproduction check for a model that is. A five-minute quick check is far cheaper than a wasted first seed iteration.

## No Skip Waiver

This step has no skip waiver. A baseline strategy decision is required before seed-design may proceed. The dialogue is typically 5–15 exchanges. The cost of skipping is a first seed task with no grounded verification target, which propagates as unverified assumption through every downstream result.

## Artifact

Write the output to `docs/baseline_strategy.md` in the run directory using the template at `docs/run_templates/baseline_strategy_template.md`.

The Baseline Strategy Gate (`python scripts/check_baseline_strategy.py --run <run-dir>`) reads this file and checks that:

1. `## Decision` is set to `variation` or `new model`
2. The corresponding target section has non-placeholder content
3. A pass criterion is stated

## Executing the Chosen Target

Once the strategy is decided, the actual execution of the reproduce or analytical verification task is done using the **`baseline-validation`** skill. The `baseline_strategy.md` defines **what** to verify; `baseline-validation` defines **how** to run and record the check.

## Cartographer Update

After writing `docs/baseline_strategy.md`, emit a `decision` node that captures the variation/new-model classification and links the verification target to its source:

- For **variation**: the decision node must carry a `cites_paper` edge to the parent paper's `paper_<paper_id>` node and a `reproduces` edge from the planned baseline result to the same paper node.
- For **new model**: the decision node must carry a `reproduces` edge from the planned baseline result to the analytical-limit target (use a stable `node_id` for the limit, e.g. `analytical_meanfield_limit`).

See `skills/cartographer-update/SKILL.md` → *Worked Examples by Lineage Kind* → "Result reproduces a paper figure". Use `decision_baseline_strategy` as the `node_id` so downstream skills can reference it.

## Suggested Next Skill

**`seed-design`** — Task 1 is automatically defined by the decision in `docs/baseline_strategy.md`.
