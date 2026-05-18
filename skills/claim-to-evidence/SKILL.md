---
name: claim-to-evidence
description: Use when reviewing abstracts, introductions, results, discussions, conclusions, captions, manuscript text, or any scientific claim that needs evidence mapping.
---

# Claim-to-Evidence Skill

Use this skill when reviewing manuscript text, abstracts, introductions, results, discussions, or conclusions.

## Goal

Ensure every scientific claim is supported by an appropriate form of evidence.

## Claim Types

1. Definition
2. Assumption
3. Analytical result
4. Numerical result
5. Empirical result
6. Comparative result
7. Scaling claim
8. Mechanistic interpretation
9. Universality claim
10. Novelty claim
11. Limitation

## Evidence Types

Acceptable support includes:

- derivation
- theorem
- equation
- simulation result
- numerical convergence test
- experimental data
- figure
- table
- benchmark comparison
- citation
- explicitly stated assumption

## Red Flags

Mark a claim as risky if it:

- claims universality from one parameter regime
- claims causality from correlation
- claims mechanism from visual pattern only
- ignores boundary or initial conditions
- ignores finite-size or finite-time effects
- omits uncertainty
- uses undefined variables
- uses ambiguous terms such as "significant", "robust", or "emergent" without support

## Output Format

| Claim | Type | Evidence | Status | Revision |
|---|---|---|---|---|

## Meeting Trigger

If any claim is typed as `Mechanistic interpretation`, `Universality claim`, or `Novelty claim` — or if its claim ceiling would be `mechanism` or above — recommend a meeting before finalizing:

```
Recommend: meeting --scope review --on "<the specific claim and its current evidence>"
```

Use `--scope review` (not `quick`) because the Peer-Review Professor's adversarial stance is specifically designed for this moment: a claim at `mechanism` or above asserts causation or generality, and those are exactly the claims most likely to be overclaimed under confirmation bias. The professor alone may be too familiar with the project to catch it.

## Status options

- Supported
- Partially supported
- Unsupported
- Overclaimed
- Needs derivation
- Needs citation
- Needs numerical validation
- Needs uncertainty estimate

## Cartographer Update

For every claim in the table, write a per-claim file to `docs/claims/<claim_slug>.md` containing the claim text, type, evidence, status, and any revision notes. `scripts/workflow_hooks.py` auto-detects this file and seeds a `lineage_kind="claim"` node with `requires_researcher_review=true`.

You **must** explicitly emit edges that anchor the claim to its supporting and limiting evidence — the filesystem can't infer these:

- `supports` edge from the claim node to each `result_*` node that backs it (or `contradicts` if a result undermines it).
- `cites_paper` edge from the claim node to each `paper_<paper_id>` node cited.
- `limits` edge from any active `anomaly_*` node to this claim if the anomaly's resolution would change the claim's status.
- `claim_ceiling` field set to the highest level the evidence supports: `observation` / `interpretation` / `mechanism` / `generalization` / `unsupported`.

Use `claim_<claim_slug>` as the `node_id` to match the auto-emitted claim node. See `skills/cartographer-update/SKILL.md` for the JSON shape; the `supports` / `contradicts` / `cites_paper` / `limits` relations are all listed in the worked examples.
