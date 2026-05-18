#!/usr/bin/env python3
"""Update workflow_map.live.json in a run directory from a Cartographer event packet.

Agents call this script to push live research state directly into the JSON file
that workflow_map.html polls every 10 seconds. No intermediate markdown parsing
is required: the HTML updates in the researcher's browser within one poll cycle.

The live_workflow_diagram.md Markdown file remains the human-readable research
log; this script is the machine path that keeps the browser view current.

Usage examples
--------------
# Update a gate status:
    python scripts/update_live_json.py --run <run-dir> \\
        --gate "Stage 1" --status pass --note "HVG chi2 p>=0.38"

# Update the active step banner:
    python scripts/update_live_json.py --run <run-dir> \\
        --active-step "Stage 2 — synthetic experiments running"

# Push a full cartographer event packet (same JSON format as live_workflow_diagram.md):
    python scripts/update_live_json.py --run <run-dir> \\
        --event '{"cartographer_update": {"node_id": "stage2", "title": "...", ...}}'

# All three at once, and also refresh the central docs/workflow_map.live.json:
    python scripts/update_live_json.py --run <run-dir> \\
        --active-step "Stage 2" --gate "Stage 1" --status pass --note "done" \\
        --update-central
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

_X_POSITIONS = [80, 330, 580, 830]
# Map (node_type | event_type) -> lineage_kind for Lineage-tab grouping.
# Lineage kinds drive Cytoscape node shape, color, and filters. The sender may
# override by setting `lineage_kind` directly in the Cartographer packet.
_LINEAGE_KIND_BY_TYPE = {
    "question": "decision",
    "assumption": "decision",
    "decision": "decision",
    "task_seed": "decision",
    "review": "decision",
    "retrospective": "decision",
    "open_issue": "decision",
    "model": "model_version",
    "equation": "model_version",
    "parameter": "model_version",
    "baseline": "model_version",
    "validation": "result",
    "validation_gate": "gate",
    "run": "result",
    "dataset": "result",
    "figure": "figure",
    "table": "figure",
    "anomaly": "anomaly",
    "waiver": "waiver",
    "claim": "claim",
    "paper": "paper",
    "literature": "paper",
}


def _infer_lineage_kind(node_type, event_type):
    for value in (node_type, event_type):
        if not value:
            continue
        kind = _LINEAGE_KIND_BY_TYPE.get(str(value).lower())
        if kind:
            return kind
    return "decision"


_PHASE_MAP = {
    "pass": "passed",
    "passed": "passed",
    "fail": "blocked",
    "blocked": "blocked",
    "partial": "blocked",
    "waived": "waived",
    "pending": "pending",
    "active": "active",
}


# ---------------------------------------------------------------------------
# JSON load / bootstrap
# ---------------------------------------------------------------------------

def _empty_live_map(run_root: Path) -> dict:
    return {
        "id": "live_research_run",
        "title": f"Live Research Workflow: {run_root.name}",
        "active_step": "",
        "description": "Live workflow state for current research run.",
        "nodes": [],
    }


def _load_or_bootstrap(run_root: Path) -> dict:
    json_path = run_root / "workflow_map.live.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if data.get("maps"):
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    # Try the generate_workflow_map logic so dashboard links are populated.
    try:
        import generate_workflow_map as gwm  # noqa: PLC0415

        original_runs_root = gwm.RUNS_ROOT
        gwm.RUNS_ROOT = run_root.parent
        try:
            live_map = gwm.live_workflow_map(base_dir=run_root)
        finally:
            gwm.RUNS_ROOT = original_runs_root
        if live_map is None:
            live_map = _empty_live_map(run_root)
        else:
            # Strip placeholder-only node lists so new updates start clean.
            nodes = live_map.get("nodes", [])
            if len(nodes) == 1 and nodes[0].get("id") == "no_active_run":
                live_map["nodes"] = []
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "maps": [live_map],
        }
    except Exception:
        pass
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maps": [_empty_live_map(run_root)],
    }


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _node_position(existing_nodes: list[dict], node_id: str, index: int) -> tuple[int, int]:
    existing = next((n for n in existing_nodes if n.get("id") == node_id), None)
    if existing:
        return existing.get("x", _X_POSITIONS[0]), existing.get("y", 90)
    x = _X_POSITIONS[index % len(_X_POSITIONS)]
    y = 90 + 170 * (index // len(_X_POSITIONS))
    return x, y


def _resolve_link(link: dict) -> dict:
    normalized = dict(link)
    path_text = str(normalized.get("path", ""))
    normalized.setdefault(
        "label",
        normalized.get("role")
        or normalized.get("kind")
        or normalized.get("relation")
        or path_text
        or "linked artifact",
    )
    return normalized


def _event_to_node(event: dict, existing_nodes: list[dict]) -> dict:
    update = event.get("cartographer_update", event)
    raw_id = update.get("node_id") or re.sub(
        r"[^a-z0-9]+",
        "_",
        str(update.get("title") or update.get("summary") or "event").lower(),
    ).strip("_")
    node_id = raw_id or "cartographer_event"

    code_links = [_resolve_link(lnk) for lnk in update.get("code_links", [])]
    result_links = [_resolve_link(lnk) for lnk in update.get("result_links", [])]
    interpretation_links = [_resolve_link(lnk) for lnk in update.get("interpretation_links", [])]

    index = next(
        (i for i, n in enumerate(existing_nodes) if n.get("id") == node_id),
        len(existing_nodes),
    )
    x, y = _node_position(existing_nodes, node_id, index)

    status = str(update.get("status", "pending")).lower()
    images = [
        lnk
        for lnk in result_links
        if str(lnk.get("kind", "")).lower() == "figure"
        or str(lnk.get("path", "")).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]

    # Lineage fields are optional; only emitted when the sender provides them.
    # They drive the Cytoscape-based Lineage tab in workflow_map.html. Existing
    # nodes without these fields render exactly as before in the flow tab.
    lineage_kind = update.get("lineage_kind")
    derived_lineage_kind = lineage_kind or _infer_lineage_kind(
        update.get("node_type"), update.get("event_type")
    )

    return {
        "id": node_id,
        "title": update.get("title") or update.get("summary") or "Cartographer Update",
        "phase": _PHASE_MAP.get(status, status),
        "node_type": update.get("node_type") or update.get("event_type") or "update",
        "link_status": update.get("link_status", "pending_review"),
        "evidence_strength": update.get("evidence_strength", "none"),
        "claim_ceiling": update.get("claim_ceiling", "unsupported"),
        "review_owner": update.get("review_owner") or update.get("from") or "unknown",
        "requires_researcher_review": bool(update.get("requires_researcher_review", False)),
        "lineage_kind": derived_lineage_kind,
        "model_version": update.get("model_version"),
        "paper_id": update.get("paper_id"),
        "thumbnail_path": update.get("thumbnail_path"),
        "parent_run": update.get("parent_run"),
        "created_at": update.get("created_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "x": x,
        "y": y,
        "summary": update.get("summary", ""),
        "result_summary": {
            "node_type": update.get("node_type") or update.get("event_type") or "update",
            "link_status": update.get("link_status", "pending_review"),
            "evidence_strength": update.get("evidence_strength", "none"),
            "claim_ceiling": update.get("claim_ceiling", "unsupported"),
            "review_owner": update.get("review_owner") or update.get("from") or "unknown",
        },
        "images": images,
        "responsible": code_links + result_links + interpretation_links,
        "code_links": code_links,
        "result_links": result_links,
        "interpretation_links": interpretation_links,
        "graph_links": update.get("graph_links", []),
        "checks": [
            "Cartographer records link state only; it does not judge scientific meaning.",
            "Open issues, stale links, waivers, and missing evidence must stay visible.",
        ],
        "edges": [
            lnk.get("to")
            for lnk in update.get("graph_links", [])
            if lnk.get("from") == node_id and lnk.get("to")
        ],
    }


def _gate_to_node(
    gate: str,
    status: str,
    note: str,
    existing_nodes: list[dict],
) -> dict:
    node_id = re.sub(r"[^a-z0-9]+", "_", gate.lower()).strip("_") or "gate"
    index = next(
        (i for i, n in enumerate(existing_nodes) if n.get("id") == node_id),
        len(existing_nodes),
    )
    x, y = _node_position(existing_nodes, node_id, index)
    existing = next((n for n in existing_nodes if n.get("id") == node_id), {})
    return {
        "id": node_id,
        "title": gate,
        "gate_status": status,
        "gate_note": note,
        "phase": _PHASE_MAP.get(status.lower(), status),
        "node_type": "validation_gate",
        "link_status": "pending_review" if status == "pending" else status,
        "evidence_strength": "none",
        "claim_ceiling": "unsupported",
        "review_owner": "lead-agent",
        "requires_researcher_review": status.lower() in {"partial", "fail", "blocked", "waived"},
        "lineage_kind": "gate",
        "x": x,
        "y": y,
        "summary": f"{status.upper()}: {note}",
        "result_summary": {},
        "images": [],
        "code_links": [],
        "result_links": [],
        "interpretation_links": [],
        "graph_links": [],
        "responsible": [],
        "checks": [
            "Cartographer records link state only; it does not judge scientific meaning.",
        ],
        "edges": existing.get("edges", []),
    }


def _upsert_node(nodes: list[dict], new_node: dict) -> list[dict]:
    for i, node in enumerate(nodes):
        if node.get("id") == new_node["id"]:
            nodes[i] = new_node
            return nodes
    nodes.append(new_node)
    return nodes


def _relink_edges(nodes: list[dict]) -> None:
    for i, node in enumerate(nodes[:-1]):
        if not node.get("edges"):
            node["edges"] = [nodes[i + 1]["id"]]


# ---------------------------------------------------------------------------
# Broken-edge linter
# ---------------------------------------------------------------------------

def find_broken_edges(run_root: Path) -> list[dict]:
    """Return graph_links / edges whose endpoints don't exist in the same map.

    Typos in `graph_links.to` are easy to make and currently fail silently
    (the Cytoscape renderer just skips the dangling edge). This linter walks
    every node in the run-local live JSON and reports any reference that
    can't be resolved against the same map's node id set.
    """
    json_path = run_root / "workflow_map.live.json"
    if not json_path.exists():
        return []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    maps = data.get("maps") or []
    if not maps:
        return []
    nodes = maps[0].get("nodes", []) or []
    ids = {n.get("id") for n in nodes if n.get("id")}
    broken: list[dict] = []
    for node in nodes:
        node_id = node.get("id") or "(missing-id)"
        for edge_id in node.get("edges", []) or []:
            if edge_id not in ids:
                broken.append({
                    "source": node_id,
                    "target": edge_id,
                    "relation": "flow",
                    "field": "edges",
                })
        for link in node.get("graph_links", []) or []:
            src = link.get("from")
            dst = link.get("to")
            rel = link.get("relation", "")
            if src and src not in ids:
                broken.append({"source": src, "target": dst, "relation": rel,
                               "field": "graph_links.from"})
            if dst and dst not in ids:
                broken.append({"source": src, "target": dst, "relation": rel,
                               "field": "graph_links.to"})
    return broken


# ---------------------------------------------------------------------------
# Public API (also usable as a library from start_research_run.py)
# ---------------------------------------------------------------------------

def bootstrap_run_json(run_root: Path) -> Path:
    """Generate an initial workflow_map.live.json for a new run directory."""
    data = _load_or_bootstrap(run_root)
    json_path = run_root / "workflow_map.live.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path


def _resolve_anomaly(nodes: list[dict], anomaly_id: str) -> int:
    """Mark all outgoing edges from a resolved anomaly node as superseded.

    Returns the number of edges that were updated. The anomaly node itself
    must have already been upserted to status=resolved by the caller — this
    helper only cleans up the dangling `limits` edges so the lineage graph
    no longer shows the threatened downstream node as still at risk.
    """
    updated = 0
    for node in nodes:
        if node.get("id") != anomaly_id:
            continue
        for link in node.get("graph_links", []) or []:
            if link.get("from") == anomaly_id and link.get("status") != "superseded":
                link["status"] = "superseded"
                updated += 1
    return updated


def _maybe_rebuild_cross_run_lineage(run_root: Path, new_node: dict) -> None:
    """Re-run build_lineage_graph.py when a packet introduces cross-run lineage.

    Best-effort. We only fire when the incoming node carries a `parent_run`
    field, since that's the only signal that affects Cross-Run Lineage tab
    edges. A run that never sets parent_run never pays this cost.
    """
    if not new_node.get("parent_run"):
        return
    script = ROOT / "scripts" / "build_lineage_graph.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--runs-root", str(run_root.parent)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: cross-run lineage rebuild failed: {exc}", file=sys.stderr)


def apply_updates(
    run_root: Path,
    *,
    active_step: str | None = None,
    gate: str | None = None,
    status: str | None = None,
    note: str = "",
    event_json: str | None = None,
) -> Path:
    """Apply one or more Cartographer updates to the run-local live JSON.

    Returns the path of the written workflow_map.live.json.
    """
    data = _load_or_bootstrap(run_root)
    live_map = data["maps"][0]
    nodes: list[dict] = live_map.setdefault("nodes", [])
    cross_run_dirty = False

    if active_step is not None:
        live_map["active_step"] = active_step

    if gate and status:
        new_node = _gate_to_node(gate, status, note, nodes)
        nodes = _upsert_node(nodes, new_node)

    if event_json:
        event = json.loads(event_json)
        new_node = _event_to_node(event, nodes)
        nodes = _upsert_node(nodes, new_node)
        # Anomaly resolution lifecycle: when an anomaly node flips to status
        # resolved, mark its outgoing limits edges as superseded so the graph
        # no longer shows the threatened downstream node as at risk.
        if new_node.get("lineage_kind") == "anomaly" and \
                str(new_node.get("phase", "")).lower() in {"resolved", "passed"}:
            _resolve_anomaly(nodes, new_node["id"])
        if new_node.get("parent_run"):
            cross_run_dirty = True

    _relink_edges(nodes)
    live_map["nodes"] = nodes
    data["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    json_path = run_root / "workflow_map.live.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    if cross_run_dirty:
        _maybe_rebuild_cross_run_lineage(run_root, new_node)
    return json_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, metavar="RUN_DIR",
                        help="Path to the research run root directory.")
    parser.add_argument("--active-step", metavar="TEXT",
                        help="Update the active-step banner shown in the HTML header.")
    parser.add_argument("--gate", metavar="NAME",
                        help="Gate name for a simple gate-status update.")
    parser.add_argument("--status", metavar="STATUS",
                        help="Gate status: pass, fail, partial, blocked, waived, pending.")
    parser.add_argument("--note", metavar="TEXT", default="",
                        help="Short note for the gate update (shown in the node summary).")
    parser.add_argument("--event", metavar="JSON",
                        help="Full cartographer_update JSON packet (same format as in "
                             "live_workflow_diagram.md Cartographer Update Events section).")
    parser.add_argument("--update-central", action="store_true",
                        help="Also regenerate docs/workflow_map.live.json via "
                             "generate_workflow_map.py after updating the run-local JSON.")
    parser.add_argument("--validate", action="store_true",
                        help="After applying updates (or with no other flags, on the "
                             "current file), check every graph_links.from/to and edges "
                             "reference against the node id set. Exits 2 on any broken "
                             "reference; otherwise prints a clean report and exits 0.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_root = Path(args.run).resolve()

    if not run_root.exists():
        print(f"ERROR: run directory not found: {run_root}", file=sys.stderr)
        return 1
    if args.gate and not args.status:
        print("ERROR: --gate requires --status", file=sys.stderr)
        return 1

    # Allow `--validate` to run on its own without requiring any update flags.
    has_update = any([args.active_step, args.gate, args.event])
    if has_update:
        try:
            json_path = apply_updates(
                run_root,
                active_step=args.active_step,
                gate=args.gate,
                status=args.status,
                note=args.note,
                event_json=args.event,
            )
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid --event JSON: {exc}", file=sys.stderr)
            return 1
        print(f"Updated: {json_path}")

    if args.validate:
        broken = find_broken_edges(run_root)
        if broken:
            print(f"Broken-edge linter found {len(broken)} dangling reference(s):",
                  file=sys.stderr)
            for b in broken:
                print(f"  - {b['field']}: {b['source']} -> {b['target']} "
                      f"(relation={b['relation']})", file=sys.stderr)
            return 2
        print("Broken-edge linter: all graph_links and edges resolve to known nodes.")

    if args.update_central:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_workflow_map.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Central map updated.")
        else:
            print(f"WARNING: generate_workflow_map.py failed:\n{result.stderr}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
