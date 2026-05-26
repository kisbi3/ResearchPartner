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

## Lineage Front-Matter

For every claim in the table, write a per-claim file to `docs/claims/<claim_slug>.md` containing the claim text, type, evidence, status, and any revision notes. Add a `lineage:` block at the top to anchor the claim to its supporting and limiting evidence:

```yaml
---
lineage:
  node_type: claim
  lineage_kind: claim
  claim_ceiling: interpretation     # observation | interpretation | mechanism | generalization | unsupported
  requires_researcher_review: true
  supports:
    - result_<slug>                 # result nodes that back this claim
  contradicts:
    - result_<other_slug>           # results that undermine it (omit if none)
  cites_paper:
    - paper_<paper_id>              # papers cited
---
```

Then run `/sync-workflow` to update the live workflow map. Note: `limits` edges belong on the anomaly node pointing to this claim, not here. See `skills/sync-workflow/SKILL.md` for the full front-matter spec.

## Finding Lifecycle

For any claim whose ceiling may become `mechanism` or `generalization`, include a
`## Finding Lifecycle` section in `docs/claims/<claim_slug>.md`. Candidate
findings cannot promote strong claims. Promotion requires declared
`independently_checked` and `evidence_linked` states, no `false_alarm` state,
and a non-empty `## Evidence Paths Read Directly` section with project paths
that exist on disk.

This is a structural gate. The checker verifies the declared lifecycle and
resolvable paths; it cannot prove that the Lead Agent actually read the files.
Do not present the checker result as proof of reading.
