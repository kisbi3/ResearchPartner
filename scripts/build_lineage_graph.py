#!/usr/bin/env python3
"""Aggregate per-run live workflow JSON into a single cross-run lineage graph.

Scans every ``ResearchPartner-runs/<run-id>/workflow_map.live.json``, prefixes
each node id with ``<run-id>__`` to avoid collisions, retargets graph_link
endpoints, adds a synthetic ``run_root`` node per run, and emits inter-run
``evolved_from`` edges wherever a node carries a ``parent_run`` field that
points at another known run.

The result is written to ``ResearchPartner-runs/_index/lineage_graph.json``
with ``display_kind: "lineage"`` so that ``workflow_map.html`` knows to render
it with the Cytoscape + dagre Lineage tab rather than the SVG flow tab.

Usage
-----
    python scripts/build_lineage_graph.py
    python scripts/build_lineage_graph.py --runs-root /abs/path/to/ResearchPartner-runs
    python scripts/build_lineage_graph.py --output some/other/path.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _default_runs_root() -> Path:
    here = Path(__file__).resolve().parents[1]
    # ResearchPartner-runs lives INSIDE the harness/project root so a downstream
    # install never spills files into its parent directory. The legacy sibling
    # location is checked as a fallback so existing runs are still aggregated
    # until the user moves them.
    in_project = here / "ResearchPartner-runs"
    if in_project.exists() or not (here.parent / "ResearchPartner-runs").exists():
        return in_project
    return here.parent / "ResearchPartner-runs"


def _safe_load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _prefix(run_id: str, node_id: str) -> str:
    return f"{run_id}__{node_id}"


def _retarget_graph_links(run_id: str, links: list[dict], known_ids: set[str]) -> list[dict]:
    out: list[dict] = []
    for link in links or []:
        src = link.get("from")
        dst = link.get("to")
        if src is None or dst is None:
            continue
        rewritten = dict(link)
        rewritten["from"] = _prefix(run_id, src) if _prefix(run_id, src) in known_ids else src
        rewritten["to"] = _prefix(run_id, dst) if _prefix(run_id, dst) in known_ids else dst
        out.append(rewritten)
    return out


def _retarget_edges(run_id: str, edges: list[str], known_ids: set[str]) -> list[str]:
    out: list[str] = []
    for eid in edges or []:
        prefixed = _prefix(run_id, eid)
        out.append(prefixed if prefixed in known_ids else eid)
    return out


def _run_root_node(run_id: str, latest_created: str | None) -> dict:
    return {
        "id": _prefix(run_id, "_run_root"),
        "title": run_id,
        "phase": "passed",
        "summary": f"Research run: {run_id}",
        "node_type": "run_root",
        "lineage_kind": "run_root",
        "link_status": "fresh",
        "evidence_strength": "none",
        "claim_ceiling": "unsupported",
        "review_owner": "lead-agent",
        "requires_researcher_review": False,
        "created_at": latest_created,
        "code_links": [],
        "result_links": [],
        "interpretation_links": [],
        "graph_links": [],
        "edges": [],
        "checks": [],
        "result_summary": {},
        "images": [],
        "run_id": run_id,
    }


def _parent_run_name(value) -> str | None:
    """Normalize a parent_run reference to a run-id (basename)."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Accept either a run-id or a path-like string; take the last segment.
    return Path(text.rstrip("/\\")).name


def aggregate(runs_root: Path) -> dict:
    nodes: list[dict] = []
    inter_run_edges: list[dict] = []
    run_ids: list[str] = []
    known_ids: set[str] = set()

    # First pass: collect all run-prefixed node ids so we can retarget links
    # even when they appear before the target in iteration order.
    discovered: list[tuple[str, Path, dict]] = []
    if runs_root.exists():
        for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir() and p.name != "_index"):
            live = run_dir / "workflow_map.live.json"
            data = _safe_load(live)
            if data is None:
                continue
            maps = data.get("maps") or []
            if not maps:
                continue
            discovered.append((run_dir.name, run_dir, maps[0]))
            run_ids.append(run_dir.name)
            known_ids.add(_prefix(run_dir.name, "_run_root"))
            for node in maps[0].get("nodes", []):
                if node.get("id"):
                    known_ids.add(_prefix(run_dir.name, node["id"]))

    # Second pass: emit prefixed nodes and gather inter-run lineage edges.
    for run_id, run_dir, live_map in discovered:
        run_root_id = _prefix(run_id, "_run_root")
        latest_created: str | None = None
        for raw in live_map.get("nodes", []):
            node = dict(raw)
            original_id = node.get("id") or "node"
            node["id"] = _prefix(run_id, original_id)
            node["run_id"] = run_id
            node["run_root"] = run_root_id
            node["graph_links"] = _retarget_graph_links(run_id, node.get("graph_links", []), known_ids)
            node["edges"] = _retarget_edges(run_id, node.get("edges", []), known_ids)
            created = node.get("created_at")
            if isinstance(created, str) and (latest_created is None or created > latest_created):
                latest_created = created
            # Convert parent_run (a run-id reference on a model_version or run-root
            # ancestry node) into a cross-run evolved_from edge.
            parent = _parent_run_name(node.get("parent_run"))
            if parent and parent in run_ids and parent != run_id:
                inter_run_edges.append({
                    "from": _prefix(parent, "_run_root"),
                    "to": node["id"],
                    "relation": "evolved_from",
                    "status": "fresh",
                })
            nodes.append(node)
        nodes.append(_run_root_node(run_id, latest_created))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maps": [
            {
                "id": "cross_run_lineage",
                "title": "Cross-Run Research Lineage",
                "description": "Aggregated lineage of every run under ResearchPartner-runs/. "
                               "Process-tracking only; does not strengthen scientific claims.",
                "display_kind": "lineage",
                "nodes": nodes,
                "inter_run_edges": inter_run_edges,
                "run_ids": run_ids,
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=Path, default=_default_runs_root(),
                        help="Root containing per-run directories (default: sibling ResearchPartner-runs).")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: <runs-root>/_index/lineage_graph.json).")
    args = parser.parse_args(argv)

    runs_root: Path = args.runs_root.resolve()
    output: Path = (args.output or (runs_root / "_index" / "lineage_graph.json")).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    data = aggregate(runs_root)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    nodes = sum(len(m.get("nodes", [])) for m in data["maps"])
    runs = len(data["maps"][0].get("run_ids", []))
    print(f"Wrote {output} ({runs} runs, {nodes} nodes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
