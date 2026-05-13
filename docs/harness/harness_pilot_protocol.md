# Harness Pilot Protocol

Use this protocol to test whether the harness is usable in a real or realistic research session.

## Goal

Evaluate whether the harness is actually followed without making the research process too heavy.

## Pilot Setup

Choose one narrow task:

- adopt the harness into an existing project
- validate one toy model
- reproduce one existing figure
- diagnose one anomalous result
- review one manuscript paragraph
- plan one simulation iteration

## Observation Checklist

During the pilot, record:

| Question | Result |
|---|---|
| Did the assistant select the right task category? | yes/no/partial |
| Did it read or apply the relevant skill? | yes/no/partial |
| Did it ask for only necessary researcher input? | yes/no/partial |
| Did it avoid premature claims? | yes/no/partial |
| Did it produce a useful artifact or log entry? | yes/no/partial |
| Did the workflow feel too heavy? | yes/no/partial |
| Did the researcher know what to do next? | yes/no/partial |

## Pilot Metrics

Record:

- time spent
- number of researcher interruptions
- artifacts created
- claims downgraded or blocked
- validation gaps found
- confusing steps
- skipped steps
- next improvement to the harness

## Pass Criteria

A pilot passes when:

- the researcher gets a useful next action
- at least one research artifact is improved or clarified
- unsupported claims are blocked or downgraded
- validation gaps are visible
- the process does not feel too heavy for the task size

## Record Results

Summarize each pilot in `docs/harness/harness_evaluation_log.md`.
