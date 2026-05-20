---
name: meeting
description: Convene a structured multi-agent review when you need external perspectives on whether something makes sense. Use when a decision, claim, model, or result needs to be challenged by someone who was not involved in producing it. Invocable at any point in the research workflow.
---

# Meeting Skill

Use this skill whenever "does this make sense?" cannot be answered reliably alone. A meeting brings in one or more outside perspectives, each taking a structured turn, and must end with a recorded resolution.

## Parameters

```
--scope   quick | review | full
--on      "<the specific question, claim, or result to evaluate>"  (required)
```

`--on` is a free-text statement of what is being reviewed. Examples:
- `--on "does the mean-field approximation hold in this parameter regime?"`
- `--on "is the claim that correlation length diverges as T→Tc justified by Fig. 2?"`
- `--on "is the variation/new-model classification in baseline_strategy.md correct?"`

## Scope

| Scope | Participants | When to use |
|---|---|---|
| `quick` | Lead Agent | Fast sanity check. One question, one challenger. Under 10 minutes. |
| `review` | Lead Agent + Peer-Review Professor | A specific claim or result needs adversarial scrutiny. |
| `full` | Professor + Peer-Review Professor + Graduate Students | High-stakes decision affecting the core claim or research direction. |

## Permission Hierarchy

| Convener | Allowed scopes | Notes |
|---|---|---|
| Graduate Student | `quick` only | Can request a meeting with the professor. Cannot convene a panel alone. |
| Lead Agent | `quick`, `review` | Can add the Peer-Review Professor. Cannot add the researcher directly. |
| Researcher | Any scope | Can convene any combination. May add custom participants beyond the defaults. |

When a graduate student needs a `review` or `full` meeting, they escalate to the Lead Agent, who then convenes it.

## Shared Context

**Always shared (all scopes):**
- `docs/process/live_workflow_diagram.md` — gives every participant a view of the current phase, gate statuses, and claim ceiling without full project history.

**Automatically surfaced based on `--on` keywords:**

| Keyword in `--on` | Additional artifact shared |
|---|---|
| model, equation, approximation | `docs/plan/model_spec.md` |
| literature, paper, prior work | `docs/literature/literature_review_plan.md` |
| baseline, reproduce, variation | `docs/plan/baseline_strategy.md` |
| result, figure, output | most recent file in `outputs/` |
| claim, evidence | `docs/plan/research_plan.md` + `docs/gates/validation_log.md` |

If the convener wants to share additional or different artifacts, they state them explicitly at the start of the meeting.

## Meeting Structure

### 1. Opening

The convener states:
- The question (`--on`)
- Who is in the room (`--scope`)
- What has been shared (workflow diagram + any additional artifact)

### 2. Participant Turns

Each participant gets one uninterrupted turn per round. Turn order:

1. **Graduate Student** (if present) — presents the work and the current best answer to `--on`
2. **Lead Agent** — Socratic or Contrarian challenge
3. **Peer-Review Professor** (if present) — adversarial review using the stances defined in `skills/peer-review-professor/SKILL.md`

Rounds continue until all objections are addressed or a disagreement is explicitly documented.

### 3. Resolution

The meeting must end with one of three outcomes:

| Outcome | Meaning |
|---|---|
| **Consensus: proceed** | All participants agree the question is resolved and work can continue |
| **Consensus: revise** | All participants agree a specific change is needed before proceeding; the change is stated explicitly |
| **Documented disagreement** | Participants cannot agree; each position is recorded with its reasoning; the researcher decides |

The resolution must be written into the meeting artifact before the skill exits. A meeting that ends without a resolution is not complete.

## Artifact

Write the meeting output to `docs/meetings/YYYY-MM-DD-<slug>.md` at the project root. Use the template at `docs/run_templates/meeting_template.md`.

The slug is derived from the first 4–5 words of `--on`.

## Suggested Follow-up

After the meeting:
- If outcome is **revise**: the specific skill that owns the artifact being revised should be re-run (e.g., `model-specification`, `baseline-strategy`, `claim-to-evidence`).
- If outcome is **documented disagreement**: add a `lineage:` front-matter block to the meeting artifact recording the open question, then run `/sync-workflow` to make it visible in the workflow diagram.
- If outcome is **proceed**: no action required — the workflow continues from where it was paused.
