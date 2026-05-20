#!/usr/bin/env python3
"""Refresh the live workflow diagram by walking the project file system.

Diagnostic replacement for the hook-driven Cartographer system.

On-demand only. Invoke from the `/sync-workflow` skill, or directly:

    python scripts/sync_workflow.py [--project <project-dir>] \\
        [--active-step "..."] [--strict] [--validate-edges]

What it does
------------
1. Walks the project's artifact directories (`docs/gates/`, `docs/plan/`,
   `docs/literature/`, `docs/model_versions/`, `literature/reviews/`,
   `docs/claims/`, `outputs/figures/`, `docs/meetings/`,
   `docs/checkpoints/`, `errors/`).
2. For each file, parses an optional ``lineage:`` YAML front-matter block
   for cross-referential edges (``evolved_from``, ``reproduces``,
   ``cites_paper``, ``supports``, ``limits``, ``contradicts``) and an
   explicit ``status`` / ``node_type`` override.
3. Rewrites ``<project>/workflow_map.live.json`` from scratch — every
   discovered artifact becomes a node, every parsed lineage entry becomes
   an edge.
4. Mirrors the inferred Active Step (when ``--active-step`` is provided)
   and the discovered Gate Status into the
   ``docs/process/live_workflow_diagram.md`` log, **preserving** the
   ``## In-Flight Tasks`` table (written by the Agent-spawn hook) and the
   ``## Real-Time Event Log`` (append-only history).

The script never spawns sub-agents and never calls an LLM. It is pure
filesystem + YAML parsing. Output is fully reproducible from the same
inputs.

Lineage front-matter spec
-------------------------
At the top of any artifact in a scanned directory, optionally include::

    ---
    lineage:
      node_type: claim                      # override default for the directory
      status: passed                        # pending|in_progress|passed|blocked|waived|resolved
      first_model_version: true             # mark this as the chain root (no evolved_from required)
      evolved_from: [model_v1]              # model-version chain edges
      reproduces: [paper_lacasa2008]        # this result reproduces a paper/baseline
      cites_paper: [paper_lacasa2008]       # this decision/claim cites a paper
      supports: [claim_universal_scaling]   # this evidence supports a claim
      contradicts: [claim_universal_scaling] # …or contradicts it
      limits: [claim_universal_scaling]     # this anomaly limits the claim
    ---

    # File body…

Files without front-matter still appear as nodes; they just have no
outgoing edges and use the directory default for ``node_type``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml  # PyYAML — required for front-matter parsing

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _layout as layout  # noqa: E402
import _project_root as project_root_mod  # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────

FIGURE_EXTS = (".png", ".pdf", ".svg", ".jpg", ".jpeg")
ERROR_EXTS = (".err",)
NODE_TYPE_PREFIX = {
    "gate": "gate",
    "plan": "plan",
    "literature": "lit",
    "model_version": "model",
    "paper": "paper",
    "claim": "claim",
    "figure": "figure",
    "anomaly": "anomaly",
    "meeting": "meeting",
    "checkpoint": "checkpoint",
    "waiver": "waiver",
}
ALLOWED_RELATIONS = {
    "evolved_from", "reproduces", "cites_paper",
    "supports", "contradicts", "limits",
}

# Gate name canonicalisation — file stem → gate name as it appears in the
# Gate Status table of live_workflow_diagram.md (case-sensitive).
GATE_STEM_TO_NAME = {
    "orient_note":            "Orient gate",
    "interview_notes":        "Interview gate",
    "literature_review_plan": "Literature review and replanning",
    "seed_design":            "Test-design seed",
    "baseline_strategy":      "Baseline or reproduction target",
    "baseline_registry":      "Baseline or reproduction target",
    "validation_log":         "Execution",
    "execution_complete":     "Execution",
    "visualization_complete": "Visualization",
    "professor_evaluation":   "Professor evaluation",
    "research_retrospective": "Completion conference",
    "user_report":            "User report",
}

# For gates whose pass criteria are encoded in a dedicated check script
# (rather than a ``Status:`` line), call the script as a subprocess.
# exit 0 → pass, any other exit → fall back to body-text inference.
GATE_STEM_TO_CHECK_SCRIPT = {
    "orient_note":            "check_orient_recorded.py",
    "interview_notes":        "check_interview_recorded.py",
    "literature_review_plan": "check_literature_reviewed.py",
    "baseline_strategy":      "check_baseline_strategy.py",
}

PHASE_MAP = {
    "pass": "passed",
    "passed": "passed",
    "fail": "blocked",
    "failed": "blocked",
    "blocked": "blocked",
    "partial": "blocked",
    "waived": "waived",
    "pending": "pending",
    "active": "active",
    "in_progress": "active",
    "in-progress": "active",
    "resolved": "passed",
    "superseded": "passed",
}

GATE_STATUS_EMOJI = {
    "pending": "",
    "in_progress": " 🔄",
    "pass": " ✓",
    "fail": " ❌",
    "blocked": " ⛔",
    "waived": " ⚠",
    "partial": " ◑",
}

X_POSITIONS = [80, 330, 580, 830]


# ── Front-matter parser ──────────────────────────────────────────────────────

_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def parse_front_matter(text: str) -> dict:
    """Return the ``lineage`` block from a YAML front-matter, or {}.

    Resilient to a missing/malformed block — returns an empty dict instead
    of raising. The block is recognised only when the file begins with
    ``---`` on line 1.
    """
    m = _FRONT_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    lineage = data.get("lineage")
    if isinstance(lineage, dict):
        return lineage
    return {}


# ── Status inference from file content ────────────────────────────────────────

_STATUS_PATTERNS = [
    (re.compile(r"^\s*(?:Status|Gate Status|Literature Gate Status)\s*[:=]\s*([A-Za-z_-]+)",
                re.IGNORECASE | re.MULTILINE),
     1),
    (re.compile(r"^##+\s*Status\s*\n+\s*([A-Za-z_-]+)",
                re.IGNORECASE | re.MULTILINE),
     1),
]


def infer_status_from_body(text: str) -> str | None:
    """Best-effort: scan markdown body for ``Status: <value>`` declarations."""
    for pattern, group in _STATUS_PATTERNS:
        m = pattern.search(text)
        if m:
            raw = m.group(group).strip().lower()
            if raw in PHASE_MAP or raw in ("ready", "complete"):
                return "passed" if raw in ("ready", "complete") else raw
    return None


# ── Project walk ──────────────────────────────────────────────────────────────


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "node"


def node_id_for(node_type: str, stem: str) -> str:
    prefix = NODE_TYPE_PREFIX.get(node_type, node_type)
    return f"{prefix}_{slug(stem)}"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _walk_md_dir(project: Path, rel: str, default_type: str) -> list[dict]:
    """Discover .md files in <project>/<rel>/ and turn each into a raw record."""
    base = project / rel
    out: list[dict] = []
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*.md")):
        text = _read(p)
        fm = parse_front_matter(text)
        stem = p.stem
        node_type = str(fm.get("node_type") or default_type)
        # Waiver files override their containing directory's default type.
        if stem.endswith("_waiver"):
            node_type = "waiver"
        out.append({
            "path": p.relative_to(project).as_posix(),
            "stem": stem,
            "node_type": node_type,
            "front_matter": fm,
            "body_status": infer_status_from_body(text),
        })
    return out


def _walk_figures(project: Path) -> list[dict]:
    base = layout.outputs_dir(project) / "figures"
    out: list[dict] = []
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in FIGURE_EXTS:
            continue
        out.append({
            "path": p.relative_to(project).as_posix(),
            "stem": p.stem,
            "node_type": "figure",
            "front_matter": {},
            "body_status": "pending",
        })
    return out


def _walk_errors(project: Path) -> list[dict]:
    base = layout.errors_dir(project)
    out: list[dict] = []
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in ERROR_EXTS:
            continue
        out.append({
            "path": p.relative_to(project).as_posix(),
            "stem": p.stem,
            "node_type": "anomaly",
            "front_matter": {},
            "body_status": "blocked",
        })
    return out


def collect_artifacts(project: Path) -> list[dict]:
    """Walk every scanned directory and return raw artifact records."""
    records: list[dict] = []
    records += _walk_md_dir(project, "docs/gates", "gate")
    records += _walk_md_dir(project, "docs/plan", "plan")
    records += _walk_md_dir(project, "docs/literature", "literature")
    records += _walk_md_dir(project, "docs/model_versions", "model_version")
    records += _walk_md_dir(project, "literature/reviews", "paper")
    records += _walk_md_dir(project, "docs/claims", "claim")
    records += _walk_md_dir(project, "docs/meetings", "meeting")
    records += _walk_md_dir(project, "docs/checkpoints", "checkpoint")
    records += _walk_figures(project)
    records += _walk_errors(project)
    return records


# ── JSON node construction ────────────────────────────────────────────────────


def _phase(record: dict) -> str:
    """Derive the visual phase from front-matter, then body, then default."""
    fm = record.get("front_matter") or {}
    raw = fm.get("status") or record.get("body_status") or "pending"
    raw = str(raw).lower()
    return PHASE_MAP.get(raw, raw)


def _lineage_kind(node_type: str) -> str:
    return {
        "gate":          "gate",
        "plan":          "decision",
        "literature":    "decision",
        "model_version": "model_version",
        "paper":         "paper",
        "claim":         "claim",
        "figure":        "figure",
        "anomaly":       "anomaly",
        "meeting":       "decision",
        "checkpoint":    "decision",
        "waiver":        "waiver",
    }.get(node_type, "decision")


def _position(node_id: str, index: int) -> tuple[int, int]:
    return X_POSITIONS[index % len(X_POSITIONS)], 90 + 170 * (index // len(X_POSITIONS))


def _edges_from_lineage(node_id: str, fm: dict) -> list[dict]:
    """Map front-matter relations to graph_links."""
    edges: list[dict] = []
    for rel in ALLOWED_RELATIONS:
        targets = fm.get(rel)
        if not targets:
            continue
        if isinstance(targets, str):
            targets = [targets]
        for t in targets:
            edges.append({
                "from": node_id,
                "to": str(t),
                "relation": rel,
                "status": "fresh",
            })
    return edges


def record_to_node(record: dict, index: int) -> dict:
    fm = record.get("front_matter") or {}
    node_type = record["node_type"]
    stem = record["stem"]

    # Allow front-matter `id` override; otherwise compute deterministic id.
    node_id = str(fm.get("id") or node_id_for(node_type, stem))
    phase = _phase(record)
    lineage_kind = str(fm.get("lineage_kind") or _lineage_kind(node_type))
    edges = _edges_from_lineage(node_id, fm)

    title = str(fm.get("title") or f"{node_type.replace('_', ' ').title()}: {stem}")
    summary = str(fm.get("summary") or record["path"])
    x, y = _position(node_id, index)

    interp_links = [{
        "path": record["path"],
        "relation": "documents",
        "status": "fresh",
        "label": record["path"],
    }]

    # Figure thumbnails get a separate result_links entry so the Lineage tab
    # can render a preview tile.
    result_links: list[dict] = []
    images: list[dict] = []
    if node_type == "figure":
        result_links.append({
            "path": record["path"],
            "kind": "figure",
            "relation": "generated_by",
            "status": "fresh",
            "label": record["path"],
        })
        images = [result_links[0]]

    node: dict = {
        "id": node_id,
        "title": title,
        "phase": phase,
        "node_type": node_type,
        "link_status": "pending_review" if phase == "pending" else "fresh",
        "evidence_strength": str(fm.get("evidence_strength") or "none"),
        "claim_ceiling": str(fm.get("claim_ceiling") or "unsupported"),
        "review_owner": str(fm.get("review_owner") or "lead-agent"),
        "requires_researcher_review": bool(fm.get("requires_researcher_review")
                                          or phase in ("pending", "blocked", "waived")),
        "lineage_kind": lineage_kind,
        "x": x,
        "y": y,
        "summary": summary,
        "result_summary": {
            "node_type": node_type,
            "link_status": "pending_review" if phase == "pending" else "fresh",
            "evidence_strength": str(fm.get("evidence_strength") or "none"),
            "claim_ceiling": str(fm.get("claim_ceiling") or "unsupported"),
            "review_owner": str(fm.get("review_owner") or "lead-agent"),
        },
        "images": images,
        "code_links": [],
        "result_links": result_links,
        "interpretation_links": interp_links,
        "responsible": interp_links + result_links,
        "graph_links": edges,
        "checks": [
            "Generated by sync-workflow from filesystem + lineage front-matter.",
            "Edges reflect explicit declarations only; absent edges do not mean none exist.",
        ],
        "edges": [e["to"] for e in edges],
    }

    # Lineage-kind specific identifying fields (paper_id, model_version,
    # thumbnail_path) so the Lineage tab can group/style nodes.
    if node_type == "paper":
        node["paper_id"] = str(fm.get("paper_id") or stem)
    if node_type == "model_version":
        node["model_version"] = str(fm.get("model_version") or stem)
        if fm.get("first_model_version"):
            node["first_model_version"] = True
    if node_type == "figure":
        node["thumbnail_path"] = record["path"]

    return node


# ── Gate-table inference ──────────────────────────────────────────────────────


def _gate_status_from_script(project: Path, stem: str) -> str | None:
    """Call a dedicated gate check function; return 'pass' on exit 0, else None.

    Imports the check module and calls main(['--project', str(project)]) directly
    rather than spawning a subprocess, which avoids the parse_args(argv or [])
    pitfall that drops sys.argv when argv is None.
    """
    script_name = GATE_STEM_TO_CHECK_SCRIPT.get(stem)
    if not script_name:
        return None
    script = Path(__file__).parent / script_name
    if not script.exists():
        return None
    import importlib.util as _ilu
    module_name = script.stem
    spec = _ilu.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        return None
    mod = _ilu.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        rc = mod.main(["--project", str(project)])
    except Exception:
        return None
    return "pass" if rc == 0 else None


def derive_gate_statuses(project: Path, records: list[dict]) -> dict[str, str]:
    """Map canonical gate name → status, derived from docs/gates/ records.

    Multiple files can feed one gate (e.g. baseline_registry.md and
    baseline_strategy.md both inform "Baseline or reproduction target");
    in that case the strongest non-pending status wins.

    For gates that have a dedicated check script (orient_note, interview_notes,
    literature_review_plan, baseline_strategy), the script is called as a
    subprocess to determine pass/fail rather than relying solely on a
    ``Status:`` body-text pattern.
    """
    strength = {"pending": 0, "in_progress": 1, "waived": 2, "blocked": 3,
                "partial": 3, "fail": 4, "passed": 5, "pass": 5}
    statuses: dict[str, str] = {}
    for rec in records:
        gate = GATE_STEM_TO_NAME.get(rec["stem"])
        if not gate:
            continue
        # Prefer the dedicated check script when available; fall back to
        # front-matter / body-text phase inference.
        script_result = _gate_status_from_script(project, rec["stem"])
        if script_result is not None:
            raw = script_result
        else:
            phase = _phase(rec)
            raw = {"passed": "pass", "blocked": "blocked", "waived": "waived",
                   "active": "in_progress", "pending": "pending"}.get(phase, phase)
        if gate not in statuses:
            statuses[gate] = raw
        elif strength.get(raw, 0) > strength.get(statuses[gate], 0):
            statuses[gate] = raw
    return statuses


# ── Markdown mirror (in-place updates) ────────────────────────────────────────


def _update_active_step_section(content: str, step: str) -> str:
    """Update only the ## Active Step section, leaving rest intact."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_section = (
        f"## Active Step\n\n"
        f"- Current step: **{step}**\n"
        f"- Current owner: lead-agent\n"
        f"- Last update: {now}\n"
    )
    pattern = re.compile(r"(^## Active Step\s*\n)(.*?)(?=^## |\Z)",
                         flags=re.MULTILINE | re.DOTALL)
    if pattern.search(content):
        return pattern.sub(new_section + "\n", content, count=1)
    return content + "\n\n" + new_section


def _update_gate_table(content: str, statuses: dict[str, str]) -> str:
    """Rewrite the Status cells of the Gate Status table in place."""
    for gate, status in statuses.items():
        emoji = GATE_STATUS_EMOJI.get(status, "")
        gate_esc = re.escape(gate)
        pattern = re.compile(rf"(\|\s*{gate_esc}\s*\|)([^|]*)(\|[^|\n]*\|)")
        replacement = rf"\1 `{status}`{emoji} \3"
        content = pattern.sub(replacement, content, count=1)
    return content


def _scaffold_diagram(project: Path) -> str:
    """Minimal live_workflow_diagram.md when none exists yet."""
    return (
        f"# Live Workflow Diagram — {project.name}\n\n"
        "Auto-managed by `scripts/sync_workflow.py` (everything except the\n"
        "In-Flight Tasks and Real-Time Event Log sections).\n\n"
        "## Active Step\n\n"
        "- Current step: (not started)\n"
        "- Current owner: lead-agent\n"
        "- Last update: never\n\n"
        "## Gate Status\n\n"
        "| Gate | Status | Note |\n"
        "|---|---|---|\n"
        "| Orient gate | pending |  |\n"
        "| Interview gate | pending |  |\n"
        "| Literature review and replanning | pending |  |\n"
        "| Test-design seed | pending |  |\n"
        "| Baseline or reproduction target | pending |  |\n"
        "| Execution | pending |  |\n"
        "| Visualization | pending |  |\n"
        "| Professor evaluation | pending |  |\n"
        "| Completion conference | pending |  |\n"
        "| User report | pending |  |\n\n"
        "## In-Flight Tasks\n\n"
        "<!-- Auto-updated by scripts/workflow_hooks.py on every Agent() spawn. -->\n\n"
        "| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n"
        "|---|---|---|---|---|---|\n\n"
        "Allowed in-flight status values: `spawned`, `acknowledged`, `abandoned`.\n\n"
        "## Real-Time Event Log\n\n"
        "<!-- Append-only. Auto-updated by scripts/workflow_hooks.py on every Agent() spawn. -->\n"
    )


def update_markdown_mirror(
    project: Path,
    statuses: dict[str, str],
    active_step: str | None,
) -> Path:
    """Update Active Step + Gate Status in place; preserve everything else."""
    md_path = layout.live_workflow_diagram(project)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    if md_path.exists():
        content = md_path.read_text(encoding="utf-8")
    else:
        content = _scaffold_diagram(project)
    if active_step is not None:
        content = _update_active_step_section(content, active_step)
    content = _update_gate_table(content, statuses)
    md_path.write_text(content, encoding="utf-8")
    return md_path


# ── JSON writer ───────────────────────────────────────────────────────────────


def _read_active_step_from_md(project: Path) -> str:
    md_path = layout.live_workflow_diagram(project)
    if not md_path.exists():
        return ""
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r"- Current step:\s*\*\*([^*\n]+)\*\*", content)
    return m.group(1).strip() if m else ""


def build_live_json(
    project: Path,
    records: list[dict],
    gate_statuses: dict[str, str],
) -> dict:
    nodes: list[dict] = []
    # Gates: one synthesised node per canonical gate, plus the underlying
    # source-file nodes for traceability.
    for index, (gate_name, status) in enumerate(gate_statuses.items()):
        node_id = node_id_for("gate", gate_name)
        phase = PHASE_MAP.get(status, status)
        x, y = _position(node_id, index)
        nodes.append({
            "id": node_id,
            "title": gate_name,
            "phase": phase,
            "node_type": "validation_gate",
            "gate_status": status,
            "link_status": "fresh" if phase == "passed" else "pending_review",
            "evidence_strength": "none",
            "claim_ceiling": "unsupported",
            "review_owner": "lead-agent",
            "requires_researcher_review": phase in ("pending", "blocked", "waived"),
            "lineage_kind": "gate",
            "x": x, "y": y,
            "summary": f"{status.upper()}",
            "result_summary": {},
            "images": [],
            "code_links": [], "result_links": [], "interpretation_links": [],
            "responsible": [],
            "graph_links": [],
            "checks": [
                "Gate status derived from docs/gates/ file contents by sync-workflow.",
            ],
            "edges": [],
        })

    base_index = len(nodes)
    for i, record in enumerate(records):
        nodes.append(record_to_node(record, base_index + i))

    return {
        "id": "live_research_run",
        "title": f"Live Research Workflow: {project.name}",
        "active_step": _read_active_step_from_md(project),
        "description": "Live workflow state for the current research project.",
        "nodes": nodes,
    }


# ── Broken-edge linter (moved from update_live_json.py) ──────────────────────


def find_broken_edges(project: Path) -> list[dict]:
    """Return graph_links / edges whose endpoints don't exist in the same map."""
    json_path = layout.workflow_map_live_json(project)
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
                broken.append({"source": node_id, "target": edge_id,
                               "relation": "flow", "field": "edges"})
        for link in node.get("graph_links", []) or []:
            src, dst, rel = link.get("from"), link.get("to"), link.get("relation", "")
            if src and src not in ids:
                broken.append({"source": src, "target": dst, "relation": rel,
                               "field": "graph_links.from"})
            if dst and dst not in ids:
                broken.append({"source": src, "target": dst, "relation": rel,
                               "field": "graph_links.to"})
    return broken


# ── Public entry point ────────────────────────────────────────────────────────


def _refresh_html(project: Path) -> None:
    """Ensure project/workflow_map.html is the current harness polling template.

    Replaces a stale generate_workflow_map.py-baked HTML (identifiable by the
    inline ``let DATA = {`` assignment) with the clean harness template that
    polls ``workflow_map.live.json`` every 10 s.  Safe to call on every sync.
    """
    project_html = project / "workflow_map.html"
    harness_html = Path(__file__).resolve().parents[1] / "workflow_map.html"
    if not harness_html.exists():
        return
    if project_html.exists():
        snippet = project_html.read_bytes()[:4096].decode("utf-8", errors="replace")
        if "let DATA = {" not in snippet:
            return  # Already the polling template; nothing to do.
    import shutil
    shutil.copy2(harness_html, project_html)


def sync(project: Path, active_step: str | None = None) -> Path:
    """Full sync: walk filesystem, write JSON, update markdown mirror."""
    records = collect_artifacts(project)
    gate_statuses = derive_gate_statuses(project, records)
    update_markdown_mirror(project, gate_statuses, active_step)
    live_map = build_live_json(project, records, gate_statuses)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maps": [live_map],
    }
    out_path = layout.workflow_map_live_json(project)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    _refresh_html(project)
    return out_path


# ── CLI ───────────────────────────────────────────────────────────────────────


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", metavar="PROJECT_DIR", default=None,
                   help="Project root. Default: walk up from cwd looking for "
                        ".research-harness marker.")
    p.add_argument("--active-step", metavar="TEXT", default=None,
                   help="Optional active-step banner override. Without this, the "
                        "existing Active Step section in the markdown is preserved.")
    p.add_argument("--validate-edges", action="store_true",
                   help="After sync, check every graph_links/edges reference "
                        "resolves to a real node id. Exit 2 on any broken edge.")
    p.add_argument("--json", action="store_true",
                   help="Print the generated live JSON path on stdout in JSON form "
                        "(machine-readable). Default is a human-readable line.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not project.exists():
        print(f"ERROR: project directory not found: {project}", file=sys.stderr)
        return 1

    out_path = sync(project, active_step=args.active_step)

    if args.json:
        print(json.dumps({"live_json": str(out_path),
                          "project": str(project)},
                         ensure_ascii=False))
    else:
        print(f"Synced workflow → {out_path}")

    if args.validate_edges:
        broken = find_broken_edges(project)
        if broken:
            print(f"\nBroken-edge linter found {len(broken)} dangling reference(s):",
                  file=sys.stderr)
            for b in broken:
                print(f"  - {b['field']}: {b['source']} -> {b['target']} "
                      f"(relation={b['relation']})", file=sys.stderr)
            return 2
        print("Broken-edge linter: all graph_links and edges resolve to known nodes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
