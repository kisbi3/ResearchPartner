# Research Run Packet Template

Use this packet for substantial research plans, reproduction attempts, validation runs, figure sets, analysis pipelines, or manuscript-claim work.

## Run Identity

- Run ID:
- Date:
- Research question:
- Physical system, model, or dataset:
- Professor Orchestrator:
- Graduate Test-Design Agents:
- Coding Subagents:
- Diagram/Cartographer Agent:

## Interview

Record only decision-relevant dialogue, not a full transcript.

### Professor Questions

- Assumption being tested:
- Missing definition:
- Risk or contradiction:

### Graduate Test-Design Notes

- Validation target:
- Observables:
- Failure criteria:
- Units or dimensions involved:
- Baseline, toy model, analytical limit, conservation check, or reproduction target:

### Coding Subagent Clarifications

- Files or scripts to touch:
- Commands to run:
- Parameters:
- Seeds:
- Outputs:

## Seed

- Testable specification:
- Assumptions:
- Boundary conditions:
- Initial conditions:
- Numerical method or analysis method:
- Claim-to-evidence path:
- First researcher review checkpoint:

## Execute

| Task | Owner | Command / Artifact | Status | Failure or Caveat |
|---|---|---|---|---|
|  |  |  | pending |  |

## Evaluate

### Graduate Validation Summary

- Baseline status:
- Dimensional status:
- Numerical status:
- Reproduction fidelity:
- Figure or table status:

### Professor Evaluation

- Does the result make physical sense?
- Did the reproduction compare against the correct target?
- What claims are supported?
- What claims are not supported?
- What must be downgraded, blocked, or re-tested?

## Completion Conference

Convene this after a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready.

| Agent | Reported Evidence | Concern | Decision Needed |
|---|---|---|---|
| Professor Orchestrator |  |  |  |
| Graduate Test-Design Agents |  |  |  |
| Coding Subagents |  |  |  |
| Diagram/Cartographer Agent |  |  |  |

## Visualization Materials

- Workflow artifact:
- Figures:
- Tables:
- Logs:
- Data products:

## Live Linked Research Graph

Use this section as the run-level index for the workflow map. Every important graph node should link code, result artifacts, and interpretation documents so the researcher can inspect the state immediately.

### Node and Relation Taxonomy

- Node types: `question`, `assumption`, `model`, `equation`, `parameter`, `baseline`, `validation`, `run`, `dataset`, `figure`, `table`, `anomaly`, `waiver`, `claim`, `decision`, `review`, `retrospective`, `open_issue`.
- Relations: `depends_on`, `implements`, `defines_parameter`, `runs_validation`, `generates_figure`, `computes_observable`, `generated_by`, `computed_from`, `supports`, `contradicts`, `limits`, `blocks`, `waived_by`, `supersedes`, `interprets`, `documents`, `requires_review`.

### Link State

- Link Status: `fresh`, `stale`, `missing`, `broken`, `pending_review`, `superseded`.
- Evidence Strength: `none`, `weak`, `moderate`, `strong`, `contradictory`.
- Claim ceiling: `observation`, `interpretation`, `mechanism`, `generalization`, `unsupported`.
- Review owner:
- Researcher Checkpoint Marker:

### Code links

| Node | Path | Line | Role | Relation | Status |
|---|---|---:|---|---|---|
|  |  |  |  |  | pending_review |

### Result links

| Node | Path | Kind | Relation | Status | Artifact Preview |
|---|---|---|---|---|---|
|  |  |  |  | pending_review |  |

### Interpretation links

| Node | Path | Anchor | Relation | Status |
|---|---|---|---|---|
|  |  |  |  | pending_review |

### Open issue nodes

| Issue | Blocks | Missing Evidence | Owner | Status |
|---|---|---|---|---|
|  |  |  |  | pending_review |

### Staleness propagation

- Code, data, parameter, or analysis changes must mark dependent figures, tables, captions, claims, and manuscript sections as `stale` until regenerated or revalidated.
- Waivers must remain visible as graph nodes and lower the claim ceiling when they limit interpretation.
- The graph should be viewable both chronologically and by evidence relation.

## User-Facing Report

### Summary

- 

### Supported Claims

- 

### Unsupported or Risky Claims

- 

### Validation Status

- 

### Caveats and Remaining Uncertainty

- 

### Next Researcher Decision

- 

## Retrospective

- What changed:
- What was learned:
- Evidence that became stronger:
- Evidence that became weaker or unchanged:
- Reusable artifact created:
- Lineage entry to preserve:
- Next smallest useful iteration:
