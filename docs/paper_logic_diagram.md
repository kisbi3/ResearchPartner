# Paper Logic Diagram

Use this before turning research output into manuscript structure.

## Paper Logic Flow

```mermaid
flowchart LR
    Q["Research question"] --> G["Literature gap"]
    G --> M["Model and assumptions"]
    M --> V["Methods and validation"]
    V --> R["Result"]
    R --> C["Claim"]
    C --> L["Limitations"]
    L --> N["Conclusion"]
```

## Claim Support Flow

```mermaid
flowchart TD
    R["Result"] --> E{"Evidence level"}
    E --> A["Exact derivation"]
    E --> B["Controlled approximation"]
    E --> C["Validated numerical result"]
    E --> D["Empirical analysis with uncertainty"]
    E --> F["Qualitative analogy"]
    E --> S["Speculation"]
    A --> W["Strong claim may be allowed"]
    B --> W
    C --> MW["Use model/regime-limited wording"]
    D --> MW
    F --> CW["Use cautious wording"]
    S --> SW["Mark explicitly as speculation"]
```

## Manuscript Section Roles

| Section | Logic Role | Gate |
|---|---|---|
| Introduction | Question and gap | Novelty needs citation support |
| Model / Theory | Assumptions and equations | Variables, units, validity regime |
| Methods | Reproducible procedure | Baseline and validation records |
| Results | Evidence | Figure/table provenance and uncertainty |
| Discussion | Interpretation | Claim-to-evidence discipline |
| Limitations | Boundaries | Negative results and open questions visible |
| Conclusion | Supported answer | No stronger than claim gate |
