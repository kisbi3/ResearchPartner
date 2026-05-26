# Finding Lifecycle

The Finding Lifecycle Hook prevents mechanism and generalization claims from
being promoted from unresolved reviewer or anomaly notes. It is intentionally a
structural gate: deterministic scripts can verify declared state, declared
direct-read paths, and file existence, but they cannot prove that the Lead Agent
actually read an artifact.

## Location

Finding lifecycle records live inside the affected claim file:

```text
docs/claims/<claim_id>.md
```

This keeps the lifecycle on the same path already covered by the wired
`docs/claims/*.md` freshness hook. Do not split finding state into a separate
directory unless the freshness hook is updated at the same time.

## States

Allowed lifecycle state tokens are:

- `candidate`
- `independently_checked`
- `validated_blocker`
- `validated_limitation`
- `false_alarm`
- `needs_researcher_judgment`
- `evidence_linked`
- `researcher_reviewed`

Mechanism and generalization promotion require a non-candidate lifecycle that
contains both `independently_checked` and `evidence_linked`, is not
`false_alarm`, and includes at least one path under `## Evidence Paths Read
Directly`.

## Enforcement Layers

`scripts/check_claim_promotion.py` is the explicit promotion gate. It preserves
the existing count and diversity thresholds, then adds lifecycle validation only
for `mechanism` and `generalization`.

`scripts/check_claim_promotion_freshness.py` is the wired `docs/claims/*.md`
write hook path used by `scripts/path_check_hooks.py`. It blocks promoted claim
writes when cited outputs are stale or missing, and for mechanism/generalization
claims it also blocks candidate-only lifecycle records and missing direct-read
paths.

Observation and interpretation claims keep the existing behavior. They are not
blocked merely because a finding lifecycle section is absent.

## Direct-Read Boundary

`Evidence Paths Read Directly` is a declaration. The checker verifies that the
list is non-empty and that every listed path resolves to an existing file inside
the project. It does not and cannot verify that the Lead Agent actually read the
file. That honesty requirement remains in the skill prose and review protocol.

## Reviewer Boundary

The peer-review confidence threshold is reviewer surface guidance, not a hard
checker. A reviewer should raise only high-confidence, scientifically material
findings with evidence paths, but no deterministic confidence checker is part of
this gate.

If peer-review output is persisted as a claim finding, use these sections:

- `## High-Signal Findings`
- `## Rejected False Positives`
- `## Needs Researcher Judgment`
- `## Evidence Paths Read Directly`

If it is not persisted, those sections are skill discipline rather than a
deterministic file check.
