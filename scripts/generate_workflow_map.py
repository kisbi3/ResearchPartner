#!/usr/bin/env python3
"""Generate the interactive workflow map HTML from docs/workflow_map.json."""

from __future__ import annotations

import html
import json
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "workflow_map.json"
OUTPUT = ROOT / "docs" / "workflow_map.html"
TEMPLATE = ROOT / "docs" / "workflow_map.template.html"
RUNS_ROOT = ROOT.parent / "ResearchPartner-runs"

DASHBOARD_DOCUMENT_GROUPS = [
    {
        "id": "needs_input",
        "title": "Needs Input",
        "description": "Documents where the researcher may need to answer, provide material, or clarify scope.",
        "documents": [
            ("Orient Note", ["docs/gates/orient_note.md", "docs/orient_note.md"]),
            ("Interview Notes", ["docs/gates/interview_notes.md", "docs/interview_notes.md"]),
            (
                "Paper Request Queue",
                ["docs/literature/paper_request_queue.md", "docs/paper_request_queue.md"],
            ),
            (
                "Literature Review Plan",
                ["docs/literature/literature_review_plan.md", "docs/literature_review_plan.md"],
            ),
            ("Meeting Notes", ["docs/meetings"]),
        ],
    },
    {
        "id": "needs_approval",
        "title": "Needs Approval",
        "description": "Documents that should be approved before the harness treats the run direction as settled.",
        "documents": [
            ("Research Plan", ["docs/plan/research_plan.md", "docs/research_plan.md"]),
            ("Model Spec", ["docs/plan/model_spec.md", "docs/model_spec.md"]),
            (
                "Baseline Strategy",
                ["docs/plan/baseline_strategy.md", "docs/baseline_strategy.md"],
            ),
            (
                "Replanning Memo",
                ["docs/literature/replanning_memo.md", "docs/replanning_memo.md"],
            ),
            (
                "Paper Logic Diagram",
                ["docs/plan/paper_logic_diagram.md", "docs/paper_logic_diagram.md"],
            ),
        ],
    },
    {
        "id": "recommended_review",
        "title": "Recommended Review",
        "description": "Documents worth checking to understand current status, evidence, decisions, and remaining risk.",
        "documents": [
            (
                "Live Workflow Diagram",
                ["docs/process/live_workflow_diagram.md", "docs/live_workflow_diagram.md"],
            ),
            ("Research State", ["docs/process/research_state.md", "docs/research_state.md"]),
            (
                "Researcher Review Log",
                ["docs/process/researcher_review_log.md", "docs/researcher_review_log.md"],
            ),
            ("Decision Log", ["docs/process/decision_log.md", "docs/decision_log.md"]),
            ("Baseline Registry", ["docs/gates/baseline_registry.md", "docs/baseline_registry.md"]),
            ("Validation Log", ["docs/gates/validation_log.md", "docs/validation_log.md"]),
            (
                "Research Retrospective",
                ["docs/process/research_retrospective.md", "docs/research_retrospective.md"],
            ),
        ],
    },
]

ACTION_GUIDANCE = {
    "Orient Note": {
        "why": "Confirm the run has a recorded task classification and first researcher-facing question.",
        "suggested_command": "python scripts/check_orient_recorded.py --run <run-dir>",
    },
    "Interview Notes": {
        "why": "Confirm the research question, assumptions, agreed direction, and next skill are recorded.",
        "suggested_command": "python scripts/check_interview_recorded.py --run <run-dir>",
    },
    "Literature Review Plan": {
        "why": "Confirm literature status before model specification or seed design relies on novelty or reproduction claims.",
        "suggested_command": "python scripts/check_literature_reviewed.py --run <run-dir>",
    },
    "Model Spec": {
        "why": "Approve the model definition before seed design or execution depends on it.",
        "suggested_command": "python scripts/check_model_specified.py --run <run-dir>",
    },
    "Baseline Strategy": {
        "why": "Approve whether this run reproduces a parent model or verifies a new analytical checkpoint.",
        "suggested_command": "python scripts/check_baseline_strategy.py --run <run-dir>",
    },
    "Baseline Registry": {
        "why": "Check that interpretation is backed by a toy model, known limit, reproduction, or explicit waiver.",
        "suggested_command": "python scripts/check_baseline_gate.py --run <run-dir>",
    },
    "Validation Log": {
        "why": "Review the current evidence chain before treating results as interpretation-ready.",
        "suggested_command": "python scripts/check_figure_provenance.py --root <run-dir>",
    },
    "Live Workflow Diagram": {
        "why": "Review active workflow state, blocked behavior, stale artifacts, and next researcher checkpoint.",
        "suggested_command": "python scripts/generate_workflow_map.py",
    },
}


def _is_document_complete(path: Path, label: str) -> bool:
    """Return True if a document has been meaningfully filled in beyond its template."""
    if path.is_dir():
        return any(path.glob("*.md"))
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")

    if label == "Orient Note":
        # Researcher Answer section must have non-comment content
        return bool(re.search(r"## Researcher Answer\s*\n\s*(?!<!--)(?!\s*$)\S", text, re.MULTILINE))

    if label == "Interview Notes":
        return bool(re.search(r"## Crystallized Research Question\s*\n\s*(?!<!--)(?!\s*$)\S", text, re.MULTILINE))

    if label == "Paper Request Queue":
        # No rows with status "open" remaining
        return not bool(re.search(r"\|\s*open\s*\|", text, re.IGNORECASE))

    if label == "Literature Review Plan":
        return bool(re.search(r"(?i)status\s*:\s*(ready|waived|pass)", text))

    if label == "Research Plan":
        # Template seed placeholder not present and file has real content
        return "Run-specific plan seed:" not in text and len(text.strip()) > 150

    if label == "Model Spec":
        # Template is mostly HTML comments; meaningful content replaces them
        non_comment = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        return len(non_comment.strip()) > 200

    if label == "Baseline Strategy":
        # Decision value appears on its own line under "## Decision"
        return bool(re.search(r"(?i)(variation|new model)", text))

    if label == "Replanning Memo":
        # Template has a seed; real memos are substantially longer
        return len(text.strip()) > 500

    return False


def dashboard_status_label(group_id: str, path: Path, label: str) -> str:
    exists = path.exists() if not path.is_dir() else any(path.iterdir())
    if not exists:
        return "Missing document"
    if group_id in {"needs_input", "needs_approval"}:
        if _is_document_complete(path, label):
            return "Completed"
        return "Needs researcher decision"
    return "Ready to review"


def dashboard_summary_key(status: str) -> str:
    return {
        "Ready to review": "ready_to_review",
        "Missing document": "missing_document",
        "Needs researcher decision": "needs_researcher_decision",
        "Completed": "completed",
    }[status]


def relative_href(path: str) -> str:
    source = ROOT / path
    return source.relative_to(OUTPUT.parent).as_posix() if source.is_relative_to(OUTPUT.parent) else Path("..", path).as_posix()


def latest_live_workflow_path() -> Path | None:
    if not RUNS_ROOT.exists():
        return None
    candidates = sorted(
        [
            *RUNS_ROOT.glob("*/docs/process/live_workflow_diagram.md"),
            *RUNS_ROOT.glob("*/docs/live_workflow_diagram.md"),
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def run_relative_path(path: Path, base_dir: Path | None = None) -> str:
    base = base_dir or OUTPUT.parent
    return Path(os.path.relpath(path, base)).as_posix()


def live_workflow_run_root(live_path: Path) -> Path:
    if live_path.parent.name == "process" and live_path.parent.parent.name == "docs":
        return live_path.parent.parent.parent
    if live_path.parent.name == "docs":
        return live_path.parent.parent
    return live_path.parents[1]


def dashboard_document_groups(run_root: Path, base_dir: Path | None = None) -> list[dict]:
    groups = []
    for group in DASHBOARD_DOCUMENT_GROUPS:
        documents = []
        for label, candidates in group["documents"]:
            candidate_paths = [run_root / candidate for candidate in candidates]
            selected = next((path for path in candidate_paths if path.exists()), candidate_paths[0])
            documents.append(
                {
                    "label": label,
                    "path": run_relative_path(selected, base_dir),
                    "status": dashboard_status_label(group["id"], selected, label),
                }
            )
        groups.append(
            {
                "id": group["id"],
                "title": group["title"],
                "description": group["description"],
                "documents": documents,
            }
        )
    return groups


def dashboard_actions(document_groups: list[dict]) -> list[dict]:
    actions = []
    for group in document_groups:
        for document in group["documents"]:
            if document["status"] == "Completed":
                continue  # completed items don't need researcher attention
            guidance = ACTION_GUIDANCE.get(document["label"], {})
            actions.append(
                {
                    "id": re.sub(
                        r"[^a-z0-9]+",
                        "_",
                        f"{group['id']}_{document['label']}".lower(),
                    ).strip("_"),
                    "title": f"Review {document['label']}",
                    "category": group["title"],
                    "status": document["status"],
                    "priority": group["id"],
                    "why": guidance.get(
                        "why",
                        "Open the linked document and decide whether this run can continue.",
                    ),
                    "suggested_command": guidance.get(
                        "suggested_command",
                        "Record the review outcome in docs/process/researcher_review_log.md",
                    ),
                    "linked_document": document,
                }
            )
    return actions


def dashboard_summary(document_groups: list[dict]) -> dict:
    summary = {}
    for group in document_groups:
        counts = {
            "ready_to_review": 0,
            "missing_document": 0,
            "needs_researcher_decision": 0,
            "completed": 0,
        }
        for doc in group["documents"]:
            counts[dashboard_summary_key(doc["status"])] += 1
        total = len(group["documents"])
        summary[group["id"]] = {
            **counts,
            "total": total,
        }
    return summary


def extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    return match.group("body").strip() if match else ""


def extract_bullet_links(
    markdown: str, run_root: Path, base_dir: Path | None = None
) -> list[dict[str, str]]:
    links = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- `") or "`" not in stripped[3:]:
            continue
        path_text = stripped.split("`", 2)[1]
        links.append(
            {
                "label": path_text,
                "path": run_relative_path(run_root / path_text, base_dir),
            }
        )
    return links


def parse_active_step(section_text: str) -> str:
    for line in section_text.splitlines():
        m = re.match(r"-\s+Current step:\s+(.+)", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def extract_gate_rows(markdown: str) -> list[dict[str, str]]:
    section = extract_section(markdown, "Gate Status")
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3 or cells[0] == "Gate":
            continue
        rows.append({"gate": cells[0], "status": cells[1].lower(), "note": cells[2]})
    return rows


def extract_json_objects(markdown: str) -> list[dict]:
    objects = []
    for match in re.finditer(r"```json\s*(?P<body>.*?)```", markdown, re.DOTALL):
        body = match.group("body").strip()
        if not body:
            continue
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    return objects


def with_run_path(link: dict, run_root: Path, base_dir: Path | None = None) -> dict:
    normalized = dict(link)
    path_text = str(normalized.get("path", ""))
    if path_text:
        normalized["path"] = run_relative_path(run_root / path_text, base_dir)
    normalized.setdefault(
        "label",
        normalized.get("role")
        or normalized.get("kind")
        or normalized.get("relation")
        or path_text
        or "linked artifact",
    )
    return normalized


def cartographer_event_nodes(
    markdown: str, run_root: Path, base_dir: Path | None = None
) -> list[dict]:
    section = extract_section(markdown, "Cartographer Update Events")
    events = []
    for value in extract_json_objects(section):
        update = value.get("cartographer_update", value)
        if isinstance(update, dict):
            events.append(update)

    nodes = []
    x_positions = [80, 330, 580, 830]
    for index, event in enumerate(events):
        node_id = event.get("node_id") or re.sub(
            r"[^a-z0-9]+",
            "_",
            str(event.get("title") or event.get("summary") or f"event_{index}").lower(),
        ).strip("_")
        code_links = [
            with_run_path(link, run_root, base_dir) for link in event.get("code_links", [])
        ]
        result_links = [
            with_run_path(link, run_root, base_dir) for link in event.get("result_links", [])
        ]
        interpretation_links = [
            with_run_path(link, run_root, base_dir)
            for link in event.get("interpretation_links", [])
        ]
        nodes.append(
            {
                "id": node_id or f"cartographer_event_{index}",
                "title": event.get("title") or event.get("summary") or "Cartographer Update",
                "phase": event.get("status", "active"),
                "node_type": event.get("node_type", event.get("event_type", "update")),
                "link_status": event.get("link_status", "pending_review"),
                "evidence_strength": event.get("evidence_strength", "none"),
                "claim_ceiling": event.get("claim_ceiling", "unsupported"),
                "review_owner": event.get("review_owner", event.get("from", "unknown")),
                "requires_researcher_review": bool(
                    event.get("requires_researcher_review", False)
                ),
                "x": x_positions[index % len(x_positions)],
                "y": 90 + 170 * (index // len(x_positions)),
                "summary": event.get("summary", ""),
                "result_summary": {
                    "node_type": event.get("node_type", event.get("event_type", "update")),
                    "link_status": event.get("link_status", "pending_review"),
                    "evidence_strength": event.get("evidence_strength", "none"),
                    "claim_ceiling": event.get("claim_ceiling", "unsupported"),
                    "review_owner": event.get("review_owner", event.get("from", "unknown")),
                },
                "images": [
                    link
                    for link in result_links
                    if str(link.get("kind", "")).lower() == "figure"
                    or str(link.get("path", "")).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
                ],
                "responsible": code_links + result_links + interpretation_links,
                "code_links": code_links,
                "result_links": result_links,
                "interpretation_links": interpretation_links,
                "graph_links": event.get("graph_links", []),
                "checks": [
                    "Cartographer records link state only; it does not judge scientific meaning.",
                    "Open issues, stale links, waivers, and missing evidence must stay visible.",
                ],
                "edges": [
                    link.get("to")
                    for link in event.get("graph_links", [])
                    if link.get("from") == node_id and link.get("to")
                ],
            }
        )
    return nodes


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def fmt_float(value: object, digits: int = 4) -> str:
    if not isinstance(value, (float, int)):
        return str(value)
    return f"{value:.{digits}g}"


def image_ref(
    run_root: Path, filename: str, label: str, base_dir: Path | None = None
) -> dict[str, str]:
    return {
        "label": label,
        "path": run_relative_path(run_root / "outputs" / filename, base_dir),
    }


# Registry mapping gate_id -> builder(run_root, base_dir) -> (fields, images).
# Add new gates by defining a builder and registering it below; the dispatcher
# (result_fields_for_gate) only does lookup, no per-gate branching.
def _baseline_fields(run_root: Path, base_dir: Path | None):
    v = read_json(run_root / "outputs" / "validation_summary.json")
    return (
        {
            "final_relative_error": fmt_float(v.get("final_relative_error")),
            "mean_drift": fmt_float(v.get("mean_drift")),
            "stability_ratio": fmt_float(v.get("stability_ratio")),
        },
        [
            image_ref(run_root, "amplitude_decay.png", "Amplitude decay", base_dir),
            image_ref(run_root, "profile_evolution.png", "Profile evolution", base_dir),
        ],
    )


def _refinement_trend_fields(run_root: Path, base_dir: Path | None):
    v = read_json(run_root / "outputs" / "validation_summary.json")
    rows = v.get("convergence", {}).get("rows", [])
    last_error = rows[-1].get("final_relative_error") if rows else ""
    return (
        {
            "grid_points": "32, 64, 128, 256",
            "finest_error": fmt_float(last_error),
            "claim_scope": "trend only",
        },
        [image_ref(run_root, "convergence_sweep.png", "Refinement trend", base_dir)],
    )


def _fixed_ratio_fields(run_root: Path, base_dir: Path | None):
    fixed = read_json(run_root / "outputs" / "fixed_ratio_convergence_summary.json")
    return (
        {
            "observed_order": fmt_float(fixed.get("observed_order")),
            "target_ratio": "0.1",
            "claim_scope": "single-mode final amplitude",
        },
        [image_ref(run_root, "fixed_ratio_convergence.png", "Fixed-ratio convergence", base_dir)],
    )


def _multimode_fields(run_root: Path, base_dir: Path | None):
    multimode = read_json(run_root / "outputs" / "multimode_validation_summary.json")
    modes = multimode.get("modes", {})
    return (
        {
            "max_relative_error": fmt_float(multimode.get("max_relative_error")),
            "mean_drift": fmt_float(multimode.get("mean_drift")),
            "modes": ", ".join(str(mode) for mode in modes.keys()),
            "claim_scope": "finite periodic sine modes",
        },
        [
            image_ref(run_root, "multimode_amplitude_decay.png", "Multi-mode amplitudes", base_dir),
            image_ref(run_root, "multimode_profile_evolution.png", "Multi-mode profile", base_dir),
        ],
    )


def _positivity_fields(run_root: Path, base_dir: Path | None):
    p = read_json(run_root / "outputs" / "positivity_validation_summary.json")
    return (
        {
            "minimum_value": fmt_float(p.get("minimum_value")),
            "mean_drift": fmt_float(p.get("mean_drift")),
            "peak_decay": fmt_float(p.get("peak_decay")),
            "claim_scope": "one smooth nonnegative periodic profile",
        },
        [
            image_ref(run_root, "positivity_profile.png", "Positivity profile", base_dir),
            image_ref(run_root, "positivity_history.png", "Positivity history", base_dir),
        ],
    )


def _dirichlet_fields(run_root: Path, base_dir: Path | None):
    d = read_json(run_root / "outputs" / "dirichlet_validation_summary.json")
    return (
        {
            "final_relative_error": fmt_float(d.get("final_relative_error")),
            "boundary_max_abs": fmt_float(d.get("boundary_max_abs")),
            "stability_ratio": fmt_float(d.get("stability_ratio")),
            "claim_scope": "one homogeneous Dirichlet sine mode",
        },
        [
            image_ref(run_root, "dirichlet_amplitude_decay.png", "Dirichlet amplitude", base_dir),
            image_ref(run_root, "dirichlet_profile_evolution.png", "Dirichlet profile", base_dir),
        ],
    )


def _anomaly_probe_fields(run_root: Path, base_dir: Path | None):
    a = read_json(run_root / "outputs" / "unstable_anomaly_probe.json")
    return (
        {
            "classification": str(a.get("classification", "")),
            "stability_ratio": fmt_float(a.get("stability_ratio")),
            "status": str(a.get("status", "")),
        },
        [],
    )


def _claim_gate_fields(run_root: Path, base_dir: Path | None):
    return (
        {
            "supported": "single-mode order claim",
            "limited": "not general robustness",
            "blocked": "arbitrary diffusion claims",
        },
        [],
    )


GATE_RESULT_BUILDERS = {
    "baseline": _baseline_fields,
    "refinement_trend": _refinement_trend_fields,
    "fixed_ratio_convergence": _fixed_ratio_fields,
    "multi_mode_validation": _multimode_fields,
    "positivity_sanity": _positivity_fields,
    "dirichlet_boundary": _dirichlet_fields,
    "anomaly_probe": _anomaly_probe_fields,
    "claim_gate": _claim_gate_fields,
}


def result_fields_for_gate(
    gate_id: str, run_root: Path, base_dir: Path | None = None
) -> tuple[dict[str, str], list[dict[str, str]]]:
    builder = GATE_RESULT_BUILDERS.get(gate_id)
    if builder is None:
        return ({}, [])
    return builder(run_root, base_dir)


def live_workflow_map(base_dir: Path | None = None) -> dict | None:
    live_path = latest_live_workflow_path()
    if live_path is None:
        return None

    run_root = live_workflow_run_root(live_path)
    markdown = live_path.read_text(encoding="utf-8", errors="ignore")
    active_step_raw = extract_section(markdown, "Active Step") or ""
    active_step = parse_active_step(active_step_raw)
    checkpoint = extract_section(markdown, "Next Review Checkpoint") or "No checkpoint recorded."
    evidence_links = extract_bullet_links(
        extract_section(markdown, "Evidence Links"), run_root, base_dir
    )
    gate_rows = extract_gate_rows(markdown)
    event_nodes = cartographer_event_nodes(markdown, run_root, base_dir)

    phase_by_status = {
        "pass": "passed",
        "partial": "blocked",
        "pending": "pending",
        "fail": "blocked",
        "waived": "waived",
    }
    x_positions = [80, 330, 580, 830]
    nodes = []
    for index, row in enumerate(gate_rows):
        status = row["status"]
        gate_id = re.sub(r"[^a-z0-9]+", "_", row["gate"].lower()).strip("_")
        result_summary, images = result_fields_for_gate(gate_id, run_root, base_dir)
        nodes.append(
            {
                "id": gate_id or f"gate_{index}",
                "title": row["gate"],
                "gate_status": status,
                "gate_note": row["note"],
                "phase": phase_by_status.get(status, status or "unknown"),
                "x": x_positions[index % len(x_positions)],
                "y": 90 + 170 * (index // len(x_positions)),
                "summary": f"{status.upper()}: {row['note']}",
                "result_summary": result_summary,
                "images": images,
                "node_type": "validation_gate",
                "link_status": "pending_review" if status == "pending" else status,
                "evidence_strength": "none",
                "claim_ceiling": "unsupported",
                "review_owner": "lead-agent",
                "requires_researcher_review": status in {"partial", "fail", "blocked", "waived"},
                "code_links": [],
                "result_links": [],
                "interpretation_links": evidence_links,
                "graph_links": [],
                "responsible": evidence_links
                + [
                    {
                        "label": "Live workflow diagram",
                        "path": run_relative_path(live_path, base_dir),
                    }
                ],
                "checks": [
                    "This is a process-tracking artifact, not scientific evidence.",
                    "The live workflow must not strengthen scientific claims.",
                    f"Next checkpoint: {checkpoint}",
                ],
                "edges": [],
            }
        )

    if event_nodes:
        if nodes:
            for index, node in enumerate(event_nodes):
                node["x"] = x_positions[index % len(x_positions)]
                node["y"] = 90 + 170 * ((index + len(nodes)) // len(x_positions))
            nodes[-1]["edges"] = [event_nodes[0]["id"]]
        nodes.extend(event_nodes)

    for index, node in enumerate(nodes[:-1]):
        if not node.get("edges"):
            node["edges"] = [nodes[index + 1]["id"]]

    if not nodes:
        nodes = [
            {
                "id": "live_workflow",
                "title": "Live Workflow",
                "phase": "pending",
                "x": 80,
                "y": 90,
                "summary": active_step,
                "result_summary": {},
                "images": [],
                "node_type": "workflow_state",
                "link_status": "missing",
                "evidence_strength": "none",
                "claim_ceiling": "unsupported",
                "review_owner": "lead-agent",
                "requires_researcher_review": True,
                "code_links": [],
                "result_links": [],
                "interpretation_links": [],
                "graph_links": [],
                "responsible": [
                    {
                        "label": "Live workflow diagram",
                        "path": run_relative_path(live_path, base_dir),
                    }
                ],
                "checks": [
                    "This is a process-tracking artifact, not scientific evidence.",
                    "The live workflow must not strengthen scientific claims.",
                ],
                "edges": [],
            }
        ]

    document_groups = dashboard_document_groups(run_root, base_dir)
    return {
        "id": "live_research_run",
        "title": f"Live Research Workflow: {run_root.name}",
        "active_step": active_step,
        "description": (
            "Current run state generated from the latest live workflow artifact. "
            "This is process-tracking only and must not strengthen scientific claims."
        ),
        "dashboard": {
            "title": "Current Run Dashboard",
            "run_root": run_relative_path(run_root, base_dir),
            "document_groups": document_groups,
            "summary": dashboard_summary(document_groups),
            "actions": dashboard_actions(document_groups),
        },
        "nodes": nodes,
    }


def placeholder_live_workflow_map() -> dict:
    return {
        "id": "live_research_run",
        "title": "Live Research Workflow: no active run",
        "description": (
            "No live workflow artifact was found. Start or update a run under "
            "ResearchPartner-runs/*/docs/process/live_workflow_diagram.md."
        ),
        "nodes": [
            {
                "id": "no_active_run",
                "title": "No Active Run",
                "phase": "pending",
                "x": 80,
                "y": 90,
                "summary": "No live workflow artifact has been generated yet.",
                "result_summary": {},
                "images": [],
                "node_type": "workflow_state",
                "link_status": "missing",
                "evidence_strength": "none",
                "claim_ceiling": "unsupported",
                "review_owner": "lead-agent",
                "requires_researcher_review": True,
                "code_links": [],
                "result_links": [],
                "interpretation_links": [],
                "graph_links": [],
                "responsible": [
                    {"label": "Workflow overview", "path": "docs/workflow_overview.md"}
                ],
                "checks": [
                    "Create a run-specific live workflow artifact before treating the map as current.",
                    "This process-tracking view must not strengthen scientific claims.",
                ],
                "edges": [],
            }
        ],
    }


def build_data(include_paper_logic: bool = False, base_dir: Path | None = None) -> dict:
    source_data = json.loads(SOURCE.read_text(encoding="utf-8"))
    live_map = live_workflow_map(base_dir)
    maps = [live_map or placeholder_live_workflow_map()]
    if include_paper_logic:
        paper_logic = next(
            (
                map_data
                for map_data in source_data.get("maps", [])
                if map_data.get("id") == "paper_logic"
            ),
            None,
        )
        if paper_logic is not None:
            maps.append(paper_logic)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "maps": maps,
    }


_PLACEHOLDER_NODE_IDS = {"no_active_run", "live_workflow"}


def _run_local_json_has_real_nodes(json_path: Path) -> bool:
    """Return True if the run-local JSON was populated by update_live_json.py."""
    if not json_path.exists():
        return False
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        nodes = (data.get("maps") or [{}])[0].get("nodes", [])
        return any(n.get("id") not in _PLACEHOLDER_NODE_IDS for n in nodes)
    except (json.JSONDecodeError, IndexError, KeyError):
        return False


def write_outputs(include_paper_logic: bool = False, force: bool = False) -> list[Path]:
    written = []
    central_data = build_data(include_paper_logic=include_paper_logic, base_dir=OUTPUT.parent)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_html(central_data), encoding="utf-8")
    # Sidecar lives at workflow_map.live.json so it does not collide with the
    # static design source at docs/workflow_map.json. The HTML polls this file
    # to detect updates; the contents include a `generated_at` timestamp.
    central_json = OUTPUT.parent / "workflow_map.live.json"
    central_json.write_text(json.dumps(central_data, indent=2), encoding="utf-8")
    written.extend([OUTPUT, central_json])

    live_path = latest_live_workflow_path()
    if live_path is not None:
        run_root = live_workflow_run_root(live_path)
        run_html = run_root / "workflow_map.html"
        run_json = run_root / "workflow_map.live.json"
        if not force and _run_local_json_has_real_nodes(run_json):
            # Preserve JSON written by update_live_json.py; only refresh the HTML.
            existing_data = json.loads(run_json.read_text(encoding="utf-8"))
            run_html.write_text(build_html(existing_data), encoding="utf-8")
            written.append(run_html)
        else:
            run_data = build_data(include_paper_logic=False, base_dir=run_root)
            run_html.write_text(build_html(run_data), encoding="utf-8")
            run_json.write_text(json.dumps(run_data, indent=2), encoding="utf-8")
            written.extend([run_html, run_json])

    return written


def build_html(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    title = "Research Partner Live Workflow"
    template = TEMPLATE.read_text(encoding="utf-8")
    return template.replace("__TITLE__", html.escape(title)).replace("__DATA__", data_json)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-paper-logic",
        action="store_true",
        help="Include the paper logic workflow when manuscript planning has been requested.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the run-local workflow_map.live.json even if it was updated by "
             "update_live_json.py. Use this to re-parse live_workflow_diagram.md from scratch.",
    )
    args = parser.parse_args()
    for path in write_outputs(include_paper_logic=args.include_paper_logic, force=args.force):
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        print(f"Generated {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
