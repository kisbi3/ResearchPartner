# Professor Orchestration Design

## Scope

This design adds a multi-agent operating protocol to the Research Partner harness. The change starts with documentation and harness-evaluation coverage, not a full executable agent runtime.

The task classification is:

- Workflow visualization
- Research plan review
- Researcher review
- Harness evaluation
- Code maintenance

## Goal

Research Partner should make scientific oversight explicit. A substantial research iteration should not look like a single coding agent rushing from prompt to implementation. It should look like a small research group:

- A professor-position orchestrator owns scientific judgment, assumptions, evidence, and claim discipline.
- Graduate-student agents turn broad tasks into concrete test and validation strategies through interviews.
- Coding subagents implement bounded tasks that have already been clarified.
- A diagram/cartographer agent keeps the live workflow visible in real time.

## Operating Model

### Professor Orchestrator

The Professor Orchestrator owns the full research loop. It starts or reviews projects by holding several internal stances:

| Stance | Role | Core Question |
|---|---|---|
| Socratic Interviewer | Questions-only. Never builds. | What are you assuming? |
| Ontologist | Finds essence, not symptoms. | What is this, really? |
| Seed Architect | Crystallizes specs from dialogue. | Is this complete and unambiguous? |
| Evaluator | Performs staged verification. | Did we build the right thing? |
| Contrarian | Challenges every assumption. | What if the opposite were true? |
| Hacker | Finds unconventional paths. | What constraints are actually real? |
| Simplifier | Removes complexity. | What is the simplest thing that could work? |
| Researcher | Stops coding and investigates. | What evidence do we actually have? |
| Architect | Identifies structural causes. | If we started over, would we build it this way? |

The professor does not treat implementation success as scientific success. It checks whether the result makes physical sense, whether a reproduction actually reproduced the intended target, and whether claims are weaker than or equal to the evidence.

### Graduate Test-Design Agents

Graduate-student agents are responsible for figuring out how to test a professor-assigned task. They must interview the professor before execution to clarify:

- the physical object, model, dataset, or claim under study
- assumptions, variables, parameters, units, and boundary conditions
- baseline, toy model, analytical limit, reproduction target, or conservation check
- observables and failure criteria
- what would change the scientific interpretation

They then interview coding subagents to turn the test strategy into bounded implementation tasks. Graduate-student agents do not let coding subagents silently change physics, units, seeds, boundaries, initial conditions, or claim wording.

### Coding Subagents

Coding subagents implement narrow tasks assigned by graduate-student agents. Their outputs must include commands, parameters, seeds, files touched, validation artifacts, and failures. They should not decide that a result supports a stronger scientific claim.

### Diagram/Cartographer Agent

The Diagram/Cartographer Agent maintains the live workflow artifact while the research work proceeds. It listens to the Professor Orchestrator, Graduate Test-Design Agents, and Coding Subagents, then records:

- active step
- interview checkpoints
- seeds/specs created from dialogue
- execution tasks
- evaluation gates
- evidence links
- blocked behaviors
- next researcher review checkpoint

It may draw or update Mermaid diagrams and workflow-map inputs, but it must not give project opinions, infer mechanisms, judge scientific meaning, strengthen claims, or convert preliminary observations into conclusions. It is a shared thinking surface, not a replacement for scientific judgment.

### Completion Conference

When a reproduction, validation, figure-generation, or other substantial task is complete and visualization artifacts are ready, the Professor Orchestrator convenes a completion conference with all agents: graduate agents, coding subagents, and the Diagram/Cartographer Agent.

The final user-facing report should summarize the meeting, each agent's contribution, current workflow state, visualization materials, evidence links, supported claims, unsupported or risky claims, validation status, reproduction fidelity, failures, caveats, remaining uncertainty, and the next researcher decision.

## Evolutionary Loop

The operating loop is:

```text
Interview -> Seed -> Execute -> Evaluate
    ^                                 |
    +-------- Evolutionary Loop ------+
```

- Interview: the professor clarifies assumptions and intent with graduate-student agents; graduate-student agents clarify implementation constraints with coding subagents.
- Seed: the clarified task becomes a compact, testable specification with assumptions, units, validation target, observables, failure criteria, and evidence path.
- Execute: coding subagents perform bounded implementation or analysis work.
- Evaluate: graduate-student agents summarize validation; the professor checks physical sense, reproduction fidelity, evidence sufficiency, and claim discipline.

If evaluation exposes ambiguity, failed reproduction, dimensional risk, or unsupported interpretation, the loop returns to Interview.

## Documentation Changes

The first implementation pass should update:

- `AGENTS.md`
- `GEMINI.md`
- `docs/workflow_overview.md`
- `docs/workflow_diagrams.md`
- `docs/harness/harness_evaluation_scenarios.md`

`AGENTS.md` and `GEMINI.md` must remain synchronized.

## Harness Evaluation Changes

Harness evaluation should check behavior, not just file presence. It should include scenarios that fail or degrade when:

- a substantial task skips Professor Orchestrator review
- no graduate-student test-design step is used before coding
- a coding subagent strengthens a claim without evidence
- a reproduction is accepted without comparing to the correct target
- the Diagram/Cartographer Agent is absent during a substantial iteration
- the live workflow artifact records process state as if it were scientific evidence
- the Diagram/Cartographer Agent gives project opinions instead of only recording workflow state
- the Professor Orchestrator fails to convene a completion conference after substantial work and visualization artifacts are ready

Expected evaluation output should identify these as pass, partial, fail, or too heavy.

## Validation Plan

The minimal validation for this documentation-first change is:

- Compare `AGENTS.md` and `GEMINI.md` for identical content.
- Run the harness evaluation script.
- Run existing tests that cover workflow-map and harness-evaluation behavior.
- Confirm no `plt.show()` usage was introduced.

## Risks and Caveats

This design does not create real autonomous runtime agents. It defines the operating discipline that future tool support can enforce. The language must stay lightweight enough that researchers use it during real work rather than treating it as ceremonial overhead.

The diagram/cartographer role is intentionally constrained. Its job is to preserve visibility and traceability, not to decide what the science means.
