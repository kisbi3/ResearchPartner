#!/usr/bin/env python3
"""Seed a synthetic research run that demonstrates the Lineage tab end-to-end.

Writes ``ResearchPartner-runs/_demo_lineage/workflow_map.live.json`` containing
papers, decisions, model versions, results, figures, and claims wired together
with ``cites_paper``, ``evolved_from``, ``reproduces``, ``supports`` edges.

Run ``python scripts/build_lineage_graph.py`` afterward to merge the demo run
into the cross-run lineage graph so it appears alongside real runs.

This is illustrative only — the demo run is clearly labeled ``_demo_lineage``
and the synthetic nodes are marked with ``review_owner: demo`` so they are easy
to identify in the dashboard.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _node(node_id, title, *, kind, summary="", model_version=None, paper_id=None,
          claim_ceiling="unsupported", evidence="none", review=False, edges=()):
    return {
        "id": node_id,
        "title": title,
        "summary": summary,
        "phase": "passed",
        "node_type": kind if kind != "model_version" else "model",
        "lineage_kind": kind,
        "model_version": model_version,
        "paper_id": paper_id,
        "link_status": "fresh",
        "evidence_strength": evidence,
        "claim_ceiling": claim_ceiling,
        "review_owner": "demo",
        "requires_researcher_review": review,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_links": [],
        "result_links": [],
        "interpretation_links": [],
        "graph_links": [],
        "edges": list(edges),
        "checks": [],
        "result_summary": {},
        "images": [],
    }


def build_demo() -> dict:
    nodes = [
        _node("paper_lacasa2008", "Lacasa 2008: Visibility Graphs",
              kind="paper", paper_id="lacasa2008",
              summary="Original horizontal visibility graph definition for time series."),
        _node("paper_luque2009", "Luque 2009: HVG Properties",
              kind="paper", paper_id="luque2009",
              summary="Analytic distribution properties of HVG degree sequences."),
        _node("decision_pick_hvg", "Decision: target HVG over VG",
              kind="decision",
              summary="Use horizontal visibility graphs because they admit closed-form null."),
        _node("model_v1_baseline", "Model v1: vanilla HVG",
              kind="model_version", model_version="v1",
              summary="Baseline HVG on raw returns."),
        _node("model_v2_directional", "Model v2: directional HVG (dHVG)",
              kind="model_version", model_version="v2",
              summary="Adds direction labels to capture asymmetric visibility."),
        _node("result_v1_chi2", "Result: v1 chi-square vs null",
              kind="result", evidence="weak",
              summary="p=0.21 — cannot reject null on synthetic AR(1)."),
        _node("result_v2_chi2", "Result: v2 chi-square vs null",
              kind="result", evidence="moderate",
              summary="p=0.003 on the same synthetic series."),
        _node("figure_v2_degree", "Figure: v2 degree distribution",
              kind="figure",
              summary="dHVG in-degree histogram with theoretical overlay."),
        _node("anomaly_outlier_2020", "Anomaly: 2020 outlier batch",
              kind="anomaly", review=True,
              summary="Three trading days produce ~5x expected isolated nodes."),
        _node("claim_dhvg_better", "Claim: dHVG captures asymmetry",
              kind="claim", claim_ceiling="interpretation", evidence="moderate", review=True,
              summary="Supported by v2 chi-square on synthetic AR(1); not yet on real data."),
    ]
    edges = [
        ("decision_pick_hvg", "paper_lacasa2008",   "cites_paper"),
        ("decision_pick_hvg", "paper_luque2009",    "cites_paper"),
        ("model_v1_baseline", "decision_pick_hvg",  "depends_on"),
        ("model_v1_baseline", "paper_lacasa2008",   "reproduces"),
        ("model_v2_directional", "model_v1_baseline", "evolved_from"),
        ("result_v1_chi2",    "model_v1_baseline",  "generated_by"),
        ("result_v2_chi2",    "model_v2_directional","generated_by"),
        ("figure_v2_degree",  "result_v2_chi2",     "generated_by"),
        ("anomaly_outlier_2020", "result_v2_chi2",  "limits"),
        ("claim_dhvg_better", "result_v2_chi2",     "supports"),
        ("claim_dhvg_better", "anomaly_outlier_2020","limits"),
    ]
    by_id = {n["id"]: n for n in nodes}
    for src, dst, rel in edges:
        by_id[src]["graph_links"].append({"from": src, "to": dst, "relation": rel, "status": "fresh"})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maps": [{
            "id": "live_research_run",
            "title": "Demo Lineage Run",
            "active_step": "Demo — illustrative only",
            "description": "Synthetic lineage for documentation; not a real research run.",
            "nodes": nodes,
        }],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=Path,
                        default=Path(__file__).resolve().parents[1].parent / "ResearchPartner-runs")
    parser.add_argument("--name", default="_demo_lineage",
                        help="Run-directory name to create (default: _demo_lineage).")
    args = parser.parse_args(argv)
    out_dir = args.runs_root / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "workflow_map.live.json"
    out_path.write_text(json.dumps(build_demo(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}.")
    print(f"Next: python scripts/build_lineage_graph.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
