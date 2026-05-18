---
name: professor-interview
description: Use after task-intake to run a free-form brainstorming dialogue between the Lead Agent and the researcher. The professor probes assumptions, challenges framing, and crystallizes the research question before Specify, Seed, or literature work begins. This is the Interview phase.
---

# Professor Interview Skill

Use this skill immediately after task-intake completes the Orient phase. Do not proceed to Specify, Seed, or literature work until this skill produces a crystallized research question that the researcher has confirmed.

## Goal

Run a multi-turn Socratic dialogue between the Lead Agent and the researcher. The conversation should progressively sharpen the research question — not evaluate it, not implement it. By the end, both the professor and the researcher should be able to state the question in one clear sentence, and the researcher should feel that the question is now more precise than when they started.

## Prerequisites

Before starting:

1. Read `docs/orient_note.md` at the project root. If it is missing or blank, stop and ask the researcher to complete the Orient phase first by running the task-intake skill.
2. Note the task classification, responsible role, and the researcher's answer to the first professor question from orient_note.md. These are the starting context for the dialogue.

## How to Conduct the Dialogue

The professor does not ask a fixed sequence of questions. Instead, the professor selects a stance based on what the conversation needs at each turn.

### Professor Stances

Use these stances fluidly. A single turn may use one or blend two. Choose the stance that pushes the conversation forward most usefully at that moment.

| Stance | When to use it | Core question |
|---|---|---|
| Socratic Interviewer | Opening the dialogue, when the researcher's mental model is still unclear | What are you assuming? |
| Ontologist | When the research object or phenomenon is named but not yet understood | What is this, really? What would make it different from something adjacent? |
| Contrarian | When a framing or assumption has been accepted without pressure | What if the opposite were true? What would that look like? |
| Hacker | When constraints seem fixed but may be contingent | What constraints are actually real? Which ones could we dissolve? |
| Researcher | When the dialogue is drifting toward plans before evidence is clear | What do we actually already know? What would we need to look up? |
| Simplifier | When the question is growing complex or branching | What is the simplest version of this that still matters? |
| Architect | When the approach seems inherited rather than chosen | If we started from a blank slate today, would we frame it this way? |
| Seed Architect | When the question feels ready — use to test closure | Can I state the question back to you in one sentence? Is that the question? |

### Dialogue Tempo

- Ask one focused question per turn. Do not ask multiple questions at once.
- After the researcher answers, reflect on what the answer reveals before asking the next question. Make this reflection visible: one or two sentences noting what became clearer, what is still open, or what tension surfaced.
- Do not propose methods, tools, or solutions during the interview. If the researcher proposes implementation, acknowledge it and redirect: "Let's hold that. Before we get there — what is the phenomenon we're trying to understand?"
- If the researcher's answer opens a new uncertainty, follow it. The goal is to surface the most important open assumption, not to cover all assumptions.
- If the dialogue stalls or the researcher seems unsure, try the Simplifier or Ontologist stance to reset to a more fundamental level.

### When the Dialogue Is Complete

The interview ends when both of the following conditions are met:

1. The professor (using the Seed Architect stance) states the research question in one sentence and the researcher confirms: "Yes, that's it" (or equivalent).
2. At least one key assumption has been surfaced that was not explicit at the start.

If the researcher says "I'm not sure" or proposes a different wording after hearing the professor's summary, continue the dialogue. Do not close prematurely.

When the dialogue is complete, tell the researcher:

> "I think we have a crystallized question. Let me write the interview notes before we move on."

Then produce the interview_notes.md artifact as described below.

## Artifact: `docs/interview_notes.md`

Write the output below into `docs/interview_notes.md` at the project root. This file is the artifact checked by `scripts/check_interview_recorded.py` before Seed or Execute work may begin.

Use this structure:

```
## Crystallized Research Question

<One sentence. The most precise formulation of the research question agreed at the end of the dialogue.>

## Key Assumptions Surfaced

- <assumption 1>
- <assumption 2>
- ...

## What Was Challenged

<What framing, assumption, or approach the professor pushed back on, and what happened to it — did it survive, shift, or dissolve?>

## Agreed Direction

<One short paragraph: what the researcher and professor agreed to investigate first, and why that entry point rather than an alternative.>

## Suggested Next Skill

<Which skill to invoke next, and why — e.g., `literature-review-planning` if prior work must be surveyed first, `model-specification` if the model definition is the next open question, `seed-design` if the task is already specified well enough to run.>
```

Do not write a full transcript. The goal is a compact, readable record — the crystallized state, not the path to it.

## Next Skill

After the interview is complete, the next skill is always **`literature-review-planning`**.

This applies even if the researcher believes the literature is already known. The literature skill provides an explicit gate and a skip waiver mechanism — if the literature review is truly not needed, the researcher records a one-line reason in `docs/literature_skip_waiver.md` and the gate passes without doing the full review.

The full default chain is:

```
professor-interview → literature-review-planning → model-specification → seed-design
```

Each step can be skipped with an explicit waiver file and a stated reason:

- `docs/literature_skip_waiver.md` — skips `literature-review-planning`
- `docs/model_skip_waiver.md` — skips `model-specification`

Skipping lowers the claim ceiling: literature skip → ceiling at most `interpretation`; model skip → ceiling at most `observation`.

The only exceptions to starting with `literature-review-planning`:

- Task type is **Anomaly / bug**: go to `anomaly-debugging` first
- Task type is **Existing project onboarding**: go to `existing-research-onboarding` first

## Gate Rule

Do not proceed to Specify, Seed, or Execute before:

1. The researcher has confirmed the crystallized research question.
2. `docs/interview_notes.md` exists and contains the required sections.
3. If required: `python scripts/check_interview_recorded.py --project <project-dir>` passes.
