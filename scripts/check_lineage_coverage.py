#!/usr/bin/env python3
"""Lineage Coverage Gate — warn when skill outputs lack the edges they require.

The Cartographer Update sections in the seven research skills (literature-
review-planning, model-specification, baseline-strategy, baseline-validation,
seed-design, anomaly-debugging, claim-to-evidence) instruct agents to emit
specific edges on top of auto-seeded nodes. A skill that quietly drops its
Cartographer Update step won't fail any other check — its file still appears
in the live diagram and the Lineage tab still renders the node. This script
exists to surface that silent failure.

Rules (one rule per row in the output table):

- ``claim`` nodes must carry at least one outgoing ``supports`` or
  ``contradicts`` edge — a claim with no anchored evidence in the lineage
  graph is the prototype "unsupported claim" the harness exists to prevent.
- ``model_version`` nodes whose id is not ``model_v1`` (or any sender-marked
  ``first_model_version: true``) must carry an outgoing ``evolved_from`` edge
  — every non-initial model version should declare its parent.
- ``paper`` nodes should have at least one incoming ``cites_paper`` or
  ``reproduces`` edge — a paper with no incoming edge has been reviewed but
  no decision or result actually relies on it (orphan paper).
- ``anomaly`` nodes with status not in {``resolved``, ``superseded``} must
  carry at least one outgoing ``limits`` edge — an unresolved anomaly with
  no downstream link is invisible to reviewers.

The script is advisory by default (exit 0 with warnings on stderr). Pass
``--strict`` to make it exit 2 on any violation, which is the mode the
Stage Checkpoint Hook uses.

Usage
-----
    python scripts/check_lineage_coverage.py --run <run-dir>
    python scripts/check_lineage_coverage.py --run <run-dir> --strict
    python scripts/check_lineage_coverage.py --run <run-dir> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_live(run_root: Path) -> dict | None:
    live = run_root / "workflow_map.live.json"
    if not live.exists():
        return None
    try:
        return json.loads(live.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _outgoing_relations(node: dict, nodes_by_id: dict[str, dict]) -> set[str]:
    rels: set[str] = set()
    for link in node.get("graph_links", []) or []:
        if link.get("from") == node.get("id") and link.get("to") in nodes_by_id:
            rels.add(str(link.get("relation") or ""))
    return rels


def _incoming_relations(target_id: str, nodes_by_id: dict[str, dict]) -> set[str]:
    rels: set[str] = set()
    for n in nodes_by_id.values():
        for link in n.get("graph_links", []) or []:
            if link.get("to") == target_id and link.get("from") in nodes_by_id:
                rels.add(str(link.get("relation") or ""))
    return rels


def check(run_root: Path) -> list[dict]:
    """Return a list of violation records. Empty list means clean."""
    data = _load_live(run_root)
    if not data:
        return [{
            "node_id": "(run)",
            "lineage_kind": "(none)",
            "rule": "workflow_map.live.json missing or unreadable",
            "fix": f"Run scripts/start_research_run.py --name {run_root.name} first.",
        }]

    maps = data.get("maps") or []
    if not maps:
        return []

    nodes = maps[0].get("nodes", []) or []
    nodes_by_id = {n.get("id"): n for n in nodes if n.get("id")}
    violations: list[dict] = []

    for node in nodes:
        node_id = node.get("id") or "(missing-id)"
        kind = node.get("lineage_kind") or "(none)"
        outgoing = _outgoing_relations(node, nodes_by_id)

        if kind == "claim":
            if not (outgoing & {"supports", "contradicts"}):
                violations.append({
                    "node_id": node_id,
                    "lineage_kind": kind,
                    "rule": "claim node has no outgoing supports/contradicts edge",
                    "fix": "Run claim-to-evidence and emit a 'supports' (or 'contradicts') edge "
                           "from this claim to each result node that backs it. "
                           "See skills/cartographer-update/SKILL.md → Worked Examples.",
                })

        elif kind == "model_version":
            is_first = bool(node.get("first_model_version")) or node_id == "model_v1"
            if not is_first and "evolved_from" not in outgoing:
                violations.append({
                    "node_id": node_id,
                    "lineage_kind": kind,
                    "rule": "non-initial model_version has no outgoing evolved_from edge",
                    "fix": "Run model-specification's Cartographer Update step: emit an "
                           "'evolved_from' edge to the predecessor model_version, "
                           "or set first_model_version=true on the packet if this really is v1.",
                })

        elif kind == "paper":
            incoming = _incoming_relations(node_id, nodes_by_id)
            if not (incoming & {"cites_paper", "reproduces"}):
                violations.append({
                    "node_id": node_id,
                    "lineage_kind": kind,
                    "rule": "paper node has no incoming cites_paper or reproduces edge "
                            "(orphan paper review)",
                    "fix": "Either remove the unused review, or run literature-review-planning / "
                           "baseline-strategy and add a 'cites_paper' or 'reproduces' edge "
                           "from the decision/result that actually relies on this paper.",
                })

        elif kind == "anomaly":
            status = str(node.get("phase") or node.get("gate_status") or "").lower()
            if status not in {"resolved", "superseded", "passed"}:
                if "limits" not in outgoing:
                    violations.append({
                        "node_id": node_id,
                        "lineage_kind": kind,
                        "rule": "unresolved anomaly has no outgoing limits edge",
                        "fix": "Run anomaly-debugging's Cartographer Update step: emit a "
                               "'limits' edge from this anomaly to the result, model, or "
                               "claim it threatens. Mark status=resolved when fixed.",
                    })

    return violations


def _format_text(violations: list[dict]) -> str:
    if not violations:
        return "Lineage coverage check passed — no missing edges detected."
    lines = [
        f"Lineage coverage check found {len(violations)} issue(s):",
        "",
    ]
    for v in violations:
        lines.append(f"- [{v['lineage_kind']}] {v['node_id']}")
        lines.append(f"    Rule: {v['rule']}")
        lines.append(f"    Fix:  {v['fix']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--run", required=True, metavar="RUN_DIR",
                        help="Path to the research run root directory.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 2 on any violation (default: exit 0 with warnings).")
    parser.add_argument("--json", action="store_true",
                        help="Emit violations as JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    run_root = Path(args.run).resolve()
    if not run_root.exists():
        print(f"ERROR: run directory not found: {run_root}", file=sys.stderr)
        return 1

    violations = check(run_root)

    if args.json:
        print(json.dumps({"violations": violations}, indent=2, ensure_ascii=False))
    else:
        msg = _format_text(violations)
        if violations:
            print(msg, file=sys.stderr)
        else:
            print(msg)

    if violations and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
