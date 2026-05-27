# Research Workflow Diagrams

## Research Workflow

```mermaid
flowchart LR
    A["Orient"] --> B["Interview"]
    B --> C["Specify"]
    C --> D["Seed"]
    D --> E["Validate"]
    E --> F["Execute"]
    F --> G["Evaluate"]
    G --> H["Review"]
    H --> I["Retrospect"]
    I --> B
    G --> J{"Anomaly or overclaim?"}
    J -->|yes| B
    H --> K["Paper logic path"]
```

## Scientific-Loop Hook Diagram

```mermaid
flowchart TB
    O["Orient"] --> TH["Task Intake Hook"]
    I["Interview"] --> AH["Ambiguity Hook"]
    I --> IG["Interview Gate Hook"]
    S["Specify"] --> LG["Literature Gate Hook"]
    S --> AU["Assumption/Units Hook"]
    S --> UC["Unit Conversion Hook"]
    S --> AR["Approximation Regime Hook"]
    SD["Seed"] --> GD["Graduate Student Role Hook"]
    V["Validate"] --> BG["Baseline Gate Hook"]
    V --> NS["Numerical Stability Hook"]
    V --> WV["Waiver Hook"]
    E["Execute"] --> PC["Parameter Change Hook"]
    E --> DL["Data Lineage Hook"]
    E --> FP["Figure Provenance Hook"]
    EV["Evaluate"] --> CS["Claim Strength Hook"]
    EV --> AN["Anomaly Hook"]
    R["Review"] --> AF["Artifact Freshness Hook"]
    R --> MD["Manuscript Drift Hook"]
    RT["Retrospect"] --> RH["Retrospective Hook"]
```

## Responsibility Diagram

```mermaid
flowchart TB
    W["Workflow node"] --> S["Skill"]
    W --> D["Doc or log"]
    W --> C["Script"]
    S --> R["Required behavior"]
    D --> P["Persistent research memory"]
    C --> V["Validation or generation"]
```

## Gate Diagram

```mermaid
flowchart TD
    O["Orient"] --> OG{"Orient note recorded?"}
    OG -->|no| OGR["Record task classification and first professor question"]
    OG -->|yes| I{"Interview gate passed?"}
    I -->|no| IN["Record crystallized question, assumptions, agreed direction, and next skill"]
    I -->|yes| L{"Literature gate ready or waived?"}
    L -->|no| LP["Plan prior-work metrics and minimum reproduction target"]
    L -->|yes| P["Plan"]
    P --> B{"Baseline identified?"}
    B -->|no| BP["Revise plan"]
    B -->|yes| V{"Baseline passed or waived?"}
    V -->|no| BV["Run toy, known limit, reproduction, or conservation check"]
    V -->|yes| E["Execute iteration"]
    E --> C{"Claim proposed?"}
    C -->|no| R["Researcher review"]
    C -->|yes| G{"Evidence sufficient?"}
    G -->|no| DW["Downgrade wording or add validation"]
    G -->|yes| RC["Record claim-to-evidence"]
```

## Professor-Led Orchestration Diagram

```mermaid
flowchart TB
    P["Lead Agent"] --> G["Graduate Student role (not spawned)"]
    P --> C["Leaf Coding Subagents"]
    P --> D["workflow_hooks.py + /sync-workflow"]
    C --> D
    D --> W["Live Workflow Artifact"]
```

## Evolutionary Loop Diagram

```mermaid
flowchart LR
    O["Orient"] --> I["Interview"]
    I --> SP["Specify"]
    SP --> S["Seed"]
    S --> V["Validate"]
    V --> E["Execute"]
    E --> EV["Evaluate"]
    EV --> R["Review"]
    R --> RT["Retrospect"]
    RT --> I
```

## Completion Conference Diagram

```mermaid
flowchart TB
    V["Visualization artifacts ready"] --> M["Completion Conference"]
    M --> R["User Report"]
```
