# Research Run Packet Template

Use this packet for substantial research plans, reproduction attempts, validation runs, figure sets, analysis pipelines, or manuscript-claim work.

## Run Identity

- Run ID:
- Date:
- Research question:
- Physical system, model, or dataset:
- Lead Agent:
- Graduate Student role passes:
- Coding Subagents:
- Cartographer (hook-driven, not spawned):

## Interview

Record only decision-relevant dialogue, not a full transcript.

### Professor Questions

- Assumption being tested:
- Missing definition:
- Risk or contradiction:

### Graduate Student Role Notes

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

## Literature Replanning Loop

Use this before full execution when novelty, reproduction targets, or prior methods affect the plan. The Lead Agent requests researcher-provided PDFs when papers are behind institutional access or otherwise unavailable to the LLM.

### Paper Request and Intake

- Paper request queue: `docs/paper_request_queue.md`
- Literature review plan: `docs/literature_review_plan.md`
- PDF directory: `literature/pdfs/`
- Paper review directory: `literature/reviews/`
- Extracted text directory: `literature/extracted_text/`
- Paper review index: `literature/index.md`
- Missing PDFs:

### Detailed Review Standard

- Each important paper needs a section-by-section paper review, not a short abstract summary.
- PDF text extraction is a reading aid, not evidence by itself; verify equations, figures, captions, tables, and claims against the PDF.
- A `Machine-Assisted Draft From Extracted Text` section may suggest candidate summary, method, result, figure/table, and reproduction leads, but it does not establish novelty or validate claims.
- `scripts/process_paper_for_review.py` may create the standard review note, extracted-text artifact, and provisional draft in one step.
- Keep clickable links across the literature graph and retain run-relative code paths beside the links so future agents can inspect details without guessing locations.
- Run `scripts/check_paper_review_quality.py` before promoting review content into the replanning memo.
- Reviews should reconstruct research context, key concepts, methods, equations, assumptions, units, figures/tables, limitations, novelty impact, and reproduction details.
- Use a Figure/Table-by-Figure/Table Review for evidence that may support claims or reproduction targets.
- Keep author claims, reviewer interpretation, and project implications separate.

### Novelty Map

| Planned Contribution | Closest Prior Work | Evidence Source | Novelty Status | Claim Ceiling |
|---|---|---|---|---|
|  |  | direct PDF / metadata / unverified | pending_review | unsupported |

### Reproduction Target

- Target paper:
- Result, figure, equation, dataset, or benchmark:
- Why this is the smallest useful reproduction target:
- Pass/fail criterion:

### Replanning Memo

- Memo path: `docs/replanning_memo.md`
- Plan changes:
- Researcher approval status:

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
| Lead Agent |  |  |  |
| Graduate Student role passes |  |  |  |
| Coding Subagents |  |  |  |
| Cartographer (hook-driven, not spawned) |  |  |  |

## Visualization Materials

- Workflow artifact:
- Figures:
- Tables:
- Logs:
- Data products:

## Live Linked Research Graph

Run-level index for the workflow map. The node/relation taxonomy, link-state vocabulary (`fresh`/`stale`/`missing`/`broken`/`pending_review`/`superseded`), evidence-strength scale, claim-ceiling scale, and staleness-propagation rules are defined in [`docs/orchestration_protocol.md`](../../../docs/orchestration_protocol.md#live-linked-research-graph) — do not duplicate them here. Fill the tables below with this run's actual links.

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
