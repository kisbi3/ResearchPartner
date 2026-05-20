---
name: harness-evaluation
description: Use when assessing whether the physics research harness is actually useful, followed, lightweight enough, or effective across realistic research scenarios.
---

# Harness Evaluation Skill

Use this skill to evaluate the harness itself.

## Goal

Determine whether the harness changes behavior in realistic research work, not merely whether files exist.

## Evaluation Layers

Evaluate three layers:

1. Structural coverage: required skills, docs, scripts, and rules exist.
2. Scenario behavior: realistic research tasks trigger the right checks and logs.
3. Usability: the workflow is small enough that a researcher would actually use it.

## Scenario Requirements

Each evaluation scenario should define:

- task prompt
- risk being tested
- expected skills
- expected docs or logs
- expected blocked behavior
- acceptable lightweight response
- failure modes

## Core Scenarios

Test at least:

1. New model without baseline
2. Existing research with old figures and unknown validation
3. Manuscript paragraph with overclaim
4. Anomalous simulation or plot
5. Numerical code change
6. End-of-iteration retrospective

## Scoring

Use:

- `pass`: required behavior is clearly enforced
- `partial`: behavior exists but is easy to skip or vague
- `fail`: behavior is absent
- `too heavy`: behavior is correct but likely too burdensome

## Output Format

### Evaluation Scope

State what was evaluated.

### Scenario Results

| Scenario | Status | Evidence | Gap |
|---|---|---|---|

### Usability Risks

List places where the harness may be too heavy, too vague, or too easy to bypass.

### Minimal Improvements

Recommend the smallest changes that improve real-world use.

### Re-evaluation Date

State when to run the evaluation again.
