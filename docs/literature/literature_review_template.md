# Literature Review Plan Template

Use this as the run-level literature plan. Write individual paper notes in `literature/reviews/` using the detailed structure below. The review should be long enough that a future researcher can reuse it without reopening the PDF for basic context.

## Research Question

- Physical system:
- Observable:
- Candidate claim:
- Current claim ceiling:
- Literature risk that could change the plan:

## Paper Intake

| Paper ID | Citation | PDF Path | Review Note | Access Status | Relevance | Review Status |
|---|---|---|---|---|---|---|
| P1 |  | `literature/pdfs/` | `literature/reviews/P1-title.md` | researcher-provided PDF / missing / metadata only |  | unread |

## Reading Priorities

- Must read before replanning:
- Can defer:
- Missing PDFs:
- Papers that may directly affect novelty:
- Papers that may provide reproduction targets:

## Detailed Paper Review Notes

Create one detailed note per important paper in `literature/reviews/`. Do not write a short abstract-only summary. The note should be a section-by-section paper review that reconstructs the paper's logic, evidence, and reusable research value.

### Required Review File Header

- Paper ID:
- Title:
- Authors / year:
- Venue:
- DOI / arXiv / URL:
- PDF path:
- Review note path:
- Review date:
- Reviewer:
- Status: reading / reviewed / needs reread / blocked by missing PDF
- Project role: foundation / closest prior work / benchmark / method / review / contradiction

### Context Summary

This block is the single source of truth for `literature/summary.md`. Keep one short line per field so the Lead Agent can load all paper summaries together without loading full reviews. Do not delete the HTML markers — `scripts/compile_literature_summary.py` reads between them.

<!-- context-summary:start -->
- **Paper ID**:
- **Title**:
- **Role in project**: foundation / closest prior / benchmark / method / contradiction
- **Claim ceiling this paper can support**: observation / interpretation / mechanism / generalization / unsupported
- **Novelty impact on our planned claim**: supports / weakens / contradicts / unrelated / unverified
- **Reproduction target**: figure/equation/dataset; pass criterion:
- **One-sentence takeaway**:
- **When NOT to rely on this paper**:
<!-- context-summary:end -->

### 0. Executive Summary

- One-paragraph summary:
- Main contribution:
- Why this paper matters for this project:
- What a future researcher should remember:
- Claim ceiling this paper can support for our project:

### 1. Research Context and Motivation

Explain the paper's problem setting rather than translating the introduction.

- Research background:
- Core problem:
- Why the problem is important:
- Limitations of prior work:
- The paper's research question:
- What to watch for while reading:

### 2. Key Concepts and Definitions

Define important terms when they first appear. Use stable names so future notes can link to them.

| Concept | Definition | Intuition | Role in Paper | Role in Our Project | Link Candidate |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### 3. Methodology

Record enough detail to reproduce or fairly compare against the method.

#### 3.1 Data, Simulation, or Model Construction

- Data source or simulated system:
- State variables and observables:
- Boundary conditions:
- Initial conditions:
- Parameter ranges:
- Units or nondimensionalization:
- Approximation regime:

#### 3.2 Proposed Method

- Method or algorithm:
- Inputs and outputs:
- Step-by-step procedure:
- Hyperparameters, tolerances, grids, timesteps, or sample sizes:
- Random seeds or stochastic elements:
- Implementation details needed for reproduction:

#### 3.3 Comparison Methods

- Baselines:
- Alternative models:
- Fairness of comparisons:
- Missing comparisons:

#### 3.4 Metrics and Validation

- Metrics:
- Statistical tests or uncertainty estimates:
- Conservation, limiting-case, or dimensional checks:
- Sensitivity or robustness checks:
- Failure criteria:

#### 3.5 Equations and Derivations

| Equation | Variables | Assumptions | Units / Dimensions | Role | Reproduction Need |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

#### 3.6 Methodological Critique

- What assumptions drive the result?
- Which choices are under-justified?
- What would change under another parameter regime?
- What details are missing for reproduction?

## Figure/Table-by-Figure/Table Review

Review every important figure and table separately. Visual agreement is not quantitative validation; record what the figure actually shows and what it does not show.

| Figure/Table | What It Shows | Inputs / Parameters | Author's Interpretation | My Interpretation | Reproduction Value | Caveats |
|---|---|---|---|---|---|---|
| Fig. 1 |  |  |  |  |  |  |

## Results Logic

- Main results in order:
- How each result supports the next:
- What the paper claims from the results:
- What the results actually establish:
- Results that are weak, missing, or ambiguous:

## Discussion and Interpretation

- Authors' central interpretation:
- Why the interpretation matters:
- Limitations acknowledged by the authors:
- Limitations not acknowledged:
- Relationship to prior literature:
- Relationship to our planned model, observable, or method:
- Possible overclaims:

## Strengths, Weaknesses, and Open Questions

### Strengths

- 

### Weaknesses

- 

### Open Questions

- 

## Reproduction Extraction

Choose the smallest reusable target this paper offers.

- Candidate reproduction target:
- Target type: figure / table / equation / dataset / benchmark / limiting case
- Required data:
- Required parameters:
- Required code or algorithm details:
- Pass/fail criterion:
- Expected failure modes:
- What this reproduction would validate:
- What it would not validate:

## Novelty and Claim Impact

| Our Planned Claim | Paper Evidence | Impact | Status | Needed Action |
|---|---|---|---|---|
|  |  | supports / weakens / contradicts / unrelated | supported / weak / contradicted / unverified |  |

## Dictionary Notes to Create

| Note Type | Candidate Title | Why Needed | Priority |
|---|---|---|---|
| Concept / Method / Metric / Model / Dataset / Mathematical Tool / Experimental Protocol / Literature Cluster |  |  |  |

## References and Further Reading

- Papers cited by this paper that we should request:
- Papers that cite this paper:
- Adjacent methods or benchmarks:
- Internal notes to link:

## Final Takeaway

- One-sentence summary:
- When to cite this paper:
- When to cite it cautiously:
- How it changes the current research plan:

## Quality Checklist

- [ ] The review is detailed enough to understand the paper's flow without reopening the PDF.
- [ ] Introduction/context explains the research problem, not just background facts.
- [ ] Important concepts are defined at first use.
- [ ] Method details include assumptions, parameters, units, and reproduction-critical settings.
- [ ] Each important figure/table is reviewed separately.
- [ ] Author claims and reviewer interpretation are separated.
- [ ] Novelty impact is based on direct PDF evidence or explicitly marked unverified.
- [ ] Reproduction target and pass/fail criterion are explicit.
- [ ] Unsupported claims are marked as `확인 필요` or `unverified`.
