# Cartographer Update Template

Use this packet when the Lead Agent, a Graduate Test-Design Agent, or a Coding Subagent needs the Cartographer (hook-driven, not spawned) to update the live workflow graph.

The sender reports facts, links, status, and limits. The Cartographer (hook-driven, not spawned) records them as graph nodes and links. It does not infer mechanisms, judge scientific meaning, or strengthen claims.

## Update Packet

```json
{
  "cartographer_update": {
    "from": "professor | graduate-test-design | coding-subagent",
    "event_type": "question | assumption | decision | task_seed | validation_gate | run | figure | table | anomaly | waiver | claim | review | retrospective | open_issue",
    "node_id": "stable-node-id",
    "title": "Short node title",
    "node_type": "question | assumption | model | equation | parameter | baseline | validation | run | dataset | figure | table | anomaly | waiver | claim | decision | review | retrospective | open_issue",
    "summary": "One-sentence factual update.",
    "status": "proposed | active | blocked | passed | failed | waived | superseded | pending_review",
    "link_status": "fresh | stale | missing | broken | pending_review | superseded",
    "evidence_strength": "none | weak | moderate | strong | contradictory",
    "claim_ceiling": "observation | interpretation | mechanism | generalization | unsupported",
    "review_owner": "professor | researcher | graduate-test-design | coding-subagent",
    "requires_researcher_review": true,
    "lineage_kind": "paper | decision | model_version | result | claim | figure | anomaly | waiver | gate",
    "model_version": "v1 | v2-with-damping | ...  (only when node_type=model/baseline)",
    "paper_id": "lacasa2008 | luque2011 | ...  (only when node_type=paper)",
    "thumbnail_path": "outputs/figures/fig3.png  (only when node_type=figure)",
    "parent_run": "ResearchPartner-runs/YYYY-MM-DD-prior-slug  (only for cross-run lineage)",
    "created_at": "2026-05-18T12:00:00+00:00  (ISO 8601; auto-stamped if omitted)",
    "code_links": [
      {
        "path": "scripts/example.py",
        "line": 1,
        "role": "what this code does for the research",
        "relation": "implements | defines_parameter | runs_validation | generates_figure | computes_observable",
        "status": "fresh | stale | missing | broken | pending_review | superseded"
      }
    ],
    "result_links": [
      {
        "path": "outputs/example.png",
        "kind": "figure | table | log | raw_data | processed_data | fit_summary",
        "relation": "generated_by | computed_from | supports | contradicts | supersedes | requires_review",
        "status": "fresh | stale | missing | broken | pending_review | superseded",
        "preview": "thumbnail | table_head | log_tail"
      }
    ],
    "interpretation_links": [
      {
        "path": "docs/validation_log.md",
        "anchor": "example-anchor",
        "relation": "interprets | limits | documents | records_decision | documents_uncertainty | requires_review",
        "status": "fresh | stale | missing | broken | pending_review | superseded"
      }
    ],
    "graph_links": [
      {
        "from": "source-node-id",
        "to": "target-node-id",
        "relation": "depends_on | supports | contradicts | limits | blocks | waived_by | supersedes | generated_by | computed_from | interprets | documents | requires_review | evolved_from | reproduces | cites_paper",
        "status": "fresh | stale | missing | broken | pending_review | superseded"
      }
    ]
  }
}
```

## Sender Checklist

- Code links point to exact files and line numbers when available.
- Result links point to inspectable artifacts, not verbal summaries.
- Interpretation links point to validation notes, decisions, caveats, reviews, or claim-to-evidence records.
- Link Status is explicit.
- Evidence Strength and claim ceiling are supplied by the Lead Agent when they affect interpretation.
- Researcher Checkpoint Marker is true for figures, claims, waivers, anomalies, stale artifacts, and unresolved open issues.
- Staleness propagation is requested when code, data, parameters, units, analysis, or plotting changed.
