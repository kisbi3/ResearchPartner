# Finding Lifecycle Template

Copy this block into `docs/claims/<claim_id>.md` for any claim that may be
promoted to `mechanism` or `generalization`.

```markdown
## Finding Lifecycle

### Finding

Status: candidate
Claim affected: <claim_id>
Evidence paths:
- docs/gates/validation_log.md

### Independent Check

Checker: scientific-validator
Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

- docs/gates/validation_log.md

### Decision

Decision: needs_researcher_judgment
Claim ceiling effect: no promotion beyond interpretation until researcher review
```

Rules:

- `candidate` cannot promote a mechanism or generalization claim.
- `false_alarm` cannot promote a mechanism or generalization claim.
- `independently_checked` and `evidence_linked` must both appear before
  promotion.
- `Evidence Paths Read Directly` must contain at least one project path that
  exists on disk.
- The checker validates declared structure only; it does not prove that the
  Lead Agent read the file.
