#!/usr/bin/env python3
"""Generate the interactive workflow map HTML from docs/workflow_map.json."""

from __future__ import annotations

import html
import json
import os
import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "workflow_map.json"
OUTPUT = ROOT / "docs" / "workflow_map.html"
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


def dashboard_status_label(group_id: str, exists: bool) -> str:
    if not exists:
        return "Missing document"
    if group_id in {"needs_input", "needs_approval"}:
        return "Needs researcher decision"
    return "Ready to review"


def dashboard_summary_key(status: str) -> str:
    return {
        "Ready to review": "ready_to_review",
        "Missing document": "missing_document",
        "Needs researcher decision": "needs_researcher_decision",
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
            exists = selected.exists()
            documents.append(
                {
                    "label": label,
                    "path": run_relative_path(selected, base_dir),
                    "status": dashboard_status_label(group["id"], exists),
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


def result_fields_for_gate(
    gate_id: str, run_root: Path, base_dir: Path | None = None
) -> tuple[dict[str, str], list[dict[str, str]]]:
    validation = read_json(run_root / "outputs" / "validation_summary.json")
    fixed = read_json(run_root / "outputs" / "fixed_ratio_convergence_summary.json")
    anomaly = read_json(run_root / "outputs" / "unstable_anomaly_probe.json")
    multimode = read_json(run_root / "outputs" / "multimode_validation_summary.json")
    positivity = read_json(run_root / "outputs" / "positivity_validation_summary.json")
    dirichlet = read_json(run_root / "outputs" / "dirichlet_validation_summary.json")

    if gate_id == "baseline":
        return (
            {
                "final_relative_error": fmt_float(validation.get("final_relative_error")),
                "mean_drift": fmt_float(validation.get("mean_drift")),
                "stability_ratio": fmt_float(validation.get("stability_ratio")),
            },
            [
                image_ref(run_root, "amplitude_decay.png", "Amplitude decay", base_dir),
                image_ref(run_root, "profile_evolution.png", "Profile evolution", base_dir),
            ],
        )
    if gate_id == "refinement_trend":
        rows = validation.get("convergence", {}).get("rows", [])
        last_error = rows[-1].get("final_relative_error") if rows else ""
        return (
            {
                "grid_points": "32, 64, 128, 256",
                "finest_error": fmt_float(last_error),
                "claim_scope": "trend only",
            },
            [image_ref(run_root, "convergence_sweep.png", "Refinement trend", base_dir)],
        )
    if gate_id == "fixed_ratio_convergence":
        return (
            {
                "observed_order": fmt_float(fixed.get("observed_order")),
                "target_ratio": "0.1",
                "claim_scope": "single-mode final amplitude",
            },
            [
                image_ref(
                    run_root, "fixed_ratio_convergence.png", "Fixed-ratio convergence", base_dir
                )
            ],
        )
    if gate_id == "multi_mode_validation":
        modes = multimode.get("modes", {})
        return (
            {
                "max_relative_error": fmt_float(multimode.get("max_relative_error")),
                "mean_drift": fmt_float(multimode.get("mean_drift")),
                "modes": ", ".join(str(mode) for mode in modes.keys()),
                "claim_scope": "finite periodic sine modes",
            },
            [
                image_ref(
                    run_root, "multimode_amplitude_decay.png", "Multi-mode amplitudes", base_dir
                ),
                image_ref(run_root, "multimode_profile_evolution.png", "Multi-mode profile", base_dir),
            ],
        )
    if gate_id == "positivity_sanity":
        return (
            {
                "minimum_value": fmt_float(positivity.get("minimum_value")),
                "mean_drift": fmt_float(positivity.get("mean_drift")),
                "peak_decay": fmt_float(positivity.get("peak_decay")),
                "claim_scope": "one smooth nonnegative periodic profile",
            },
            [
                image_ref(run_root, "positivity_profile.png", "Positivity profile", base_dir),
                image_ref(run_root, "positivity_history.png", "Positivity history", base_dir),
            ],
        )
    if gate_id == "dirichlet_boundary":
        return (
            {
                "final_relative_error": fmt_float(dirichlet.get("final_relative_error")),
                "boundary_max_abs": fmt_float(dirichlet.get("boundary_max_abs")),
                "stability_ratio": fmt_float(dirichlet.get("stability_ratio")),
                "claim_scope": "one homogeneous Dirichlet sine mode",
            },
            [
                image_ref(run_root, "dirichlet_amplitude_decay.png", "Dirichlet amplitude", base_dir),
                image_ref(run_root, "dirichlet_profile_evolution.png", "Dirichlet profile", base_dir),
            ],
        )
    if gate_id == "anomaly_probe":
        return (
            {
                "classification": str(anomaly.get("classification", "")),
                "stability_ratio": fmt_float(anomaly.get("stability_ratio")),
                "status": str(anomaly.get("status", "")),
            },
            [],
        )
    if gate_id == "claim_gate":
        return (
            {
                "supported": "single-mode order claim",
                "limited": "not general robustness",
                "blocked": "arbitrary diffusion claims",
            },
            [],
        )
    return ({}, [])


def live_workflow_map(base_dir: Path | None = None) -> dict | None:
    live_path = latest_live_workflow_path()
    if live_path is None:
        return None

    run_root = live_workflow_run_root(live_path)
    markdown = live_path.read_text(encoding="utf-8", errors="ignore")
    active_step = extract_section(markdown, "Active Step") or "No active step recorded."
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
                "review_owner": "professor",
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
                "review_owner": "professor",
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
                "review_owner": "professor",
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
    return {"maps": maps}


def write_outputs(include_paper_logic: bool = False) -> list[Path]:
    written = []
    central_data = build_data(include_paper_logic=include_paper_logic, base_dir=OUTPUT.parent)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_html(central_data), encoding="utf-8")
    written.append(OUTPUT)

    live_path = latest_live_workflow_path()
    if live_path is not None:
        run_root = live_workflow_run_root(live_path)
        run_data = build_data(include_paper_logic=False, base_dir=run_root)
        run_html = run_root / "workflow_map.html"
        run_json = run_root / "workflow_map.json"
        run_html.write_text(build_html(run_data), encoding="utf-8")
        run_json.write_text(json.dumps(run_data, indent=2), encoding="utf-8")
        written.extend([run_html, run_json])

    return written


def build_html(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    title = "Research Partner Live Workflow"
    template = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>__TITLE__</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #202124;
      --muted: #5f6368;
      --line: #d2d7d3;
      --accent: #0f766e;
      --accent-2: #7c2d12;
      --focus: #0b57d0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      padding: 20px 24px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    h1 {{ margin: 0 0 6px; font-size: 24px; }}
    p {{ line-height: 1.45; }}
    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
      gap: 16px;
      padding: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }}
    button {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 10px;
      cursor: pointer;
      font: inherit;
    }}
    button:hover, button:focus-visible {{
      border-color: var(--focus);
      outline: none;
    }}
    button.active {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    .diagram-wrap {{ padding: 12px; overflow: auto; }}
    svg {{ width: 100%; min-width: 920px; height: 620px; }}
    .edge {{ stroke: #8c958f; stroke-width: 2; fill: none; marker-end: url(#arrow); }}
    .node rect {{ fill: #fff; stroke: #b9c3bd; stroke-width: 2; rx: 8; }}
    .node.active rect {{ stroke: var(--accent); stroke-width: 4; }}
    .node text {{ pointer-events: none; fill: var(--ink); }}
    .node .phase {{ fill: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .node .title {{ font-size: 15px; font-weight: 700; }}
    .node:hover rect {{ stroke: var(--focus); }}
    aside {{ padding: 16px; }}
    aside h2 {{ margin: 0 0 8px; font-size: 20px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin-bottom: 14px; }}
    .section {{ margin-top: 18px; }}
    .section h3 {{ margin: 0 0 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 5px 0; }}
    a {{ color: var(--accent-2); text-decoration-thickness: 1px; text-underline-offset: 2px; }}
    .docs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .docs a, .docs button {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 8px;
      text-decoration: none;
      color: var(--ink);
      background: #fbfbf8;
      font: inherit;
      cursor: pointer;
    }}
    .docs a:hover, .docs button:hover {{ border-color: var(--focus); }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    .summary-pill {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      background: #fbfbf8;
      min-width: 0;
    }}
    .summary-pill strong {{
      display: block;
      font-size: 15px;
      margin-bottom: 2px;
    }}
    .summary-pill span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
    }}
    .action-queue {{
      border-bottom: 1px solid var(--line);
      padding: 12px;
      background: #fbfbf8;
    }}
    .action-queue h2 {{
      margin: 0 0 4px;
      font-size: 15px;
    }}
    .action-help {{
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
    }}
    .next-action {{
      margin: 10px 0;
      font-size: 13px;
      font-weight: 700;
    }}
    .action-groups {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .action-group {{
      display: grid;
      gap: 6px;
      min-width: 0;
    }}
    .action-group-title {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 700;
    }}
    .action-card {{
      text-align: left;
      border-color: var(--line);
      background: #fff;
      min-height: 0;
      padding: 7px 8px;
      width: 100%;
    }}
    .action-card.active {{
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(42, 106, 79, 0.18);
    }}
    .action-card strong {{
      display: block;
      margin-bottom: 3px;
      overflow-wrap: anywhere;
      font-size: 13px;
    }}
    .action-card span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
    }}
    .command-box {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      background: #111;
      color: #fff;
      overflow-x: auto;
      font-size: 12px;
    }}
    .file-preview {{
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfbf8;
      overflow: hidden;
    }}
    .file-preview .preview-head {{
      display: flex;
      justify-content: space-between;
      gap: 8px;
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      color: var(--muted);
    }}
    .file-preview pre {{
      margin: 0;
      padding: 10px;
      max-height: 230px;
      overflow: auto;
      white-space: pre-wrap;
      font-size: 12px;
      line-height: 1.4;
    }}
    .results {{
      display: grid;
      gap: 8px;
    }}
    .result-row {{
      display: grid;
      grid-template-columns: minmax(120px, 0.55fr) minmax(0, 1fr);
      gap: 8px;
      padding: 7px 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf8;
      font-size: 13px;
    }}
    .result-key {{ color: var(--muted); }}
    .result-value {{ font-weight: 650; overflow-wrap: anywhere; }}
    .image-grid {{
      display: grid;
      gap: 10px;
    }}
    .evidence-image {{
      display: block;
      width: 100%;
      max-height: 220px;
      object-fit: contain;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }}
    .image-caption {{
      margin-top: 4px;
      font-size: 12px;
      color: var(--muted);
    }}
    .link-grid {{
      display: grid;
      gap: 8px;
    }}
    .link-card {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      background: #fbfbf8;
    }}
    .link-card a {{
      font-weight: 700;
    }}
    .link-meta {{
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    footer {{
      padding: 12px 24px 20px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 900px) {{
      .shell {{ grid-template-columns: 1fr; }}
      .action-groups, .summary-grid {{ grid-template-columns: 1fr; }}
      svg {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>__TITLE__</h1>
    <p>Click a workflow node to inspect current gates, evidence links, blocked behaviors, and next review checkpoints. This page is the live research workflow by default. Add the paper logic workflow only when the researcher explicitly starts manuscript planning. Auto-refreshes every 10 seconds after the generator updates this file.</p>
  </header>
  <main class=\"shell\">
    <section class=\"panel\">
      <div class=\"tabs\" id=\"tabs\"></div>
      <div class=\"action-queue\" id=\"actionQueue\"></div>
      <div class=\"diagram-wrap\" id=\"diagram\"></div>
    </section>
    <aside class=\"panel\" id=\"details\" aria-live=\"polite\"></aside>
  </main>
  <footer>
    Related docs: <a href=\"workflow_overview.md\">workflow_overview.md</a>,
    <a href=\"workflow_diagrams.md\">workflow_diagrams.md</a>,
    <a href=\"paper_logic_diagram.md\">paper_logic_diagram.md</a>.
  </footer>
  <script>
    const DATA = __DATA__;
    let activeMap = DATA.maps[0].id;
    let activeNode = DATA.maps[0].nodes[0].id;
    let activeAction = firstActionId(currentMap());

    function pathHref(path) {{
      const map = currentMap();
      const runLocal = Boolean(map && map.dashboard && map.dashboard.run_root === '.');
      const [base, hash] = String(path).split('#');
      let href = base;
      if (href.startsWith('../')) href = href;
      else if (href.startsWith('docs/') && !runLocal) href = href.replace(/^docs\\//, '');
      else if (runLocal) href = href;
      else href = '../' + href;
      return hash ? href + '#' + hash : href;
    }}

    function linkHref(item) {{
      const anchor = item.anchor ? '#' + item.anchor : '';
      return pathHref(String(item.path || '') + anchor);
    }}

    function currentMap() {{
      return DATA.maps.find(map => map.id === activeMap);
    }}

    function firstActionId(map) {{
      const actions = (((map || {{}}).dashboard || {{}}).actions || []);
      return actions.length ? actions[0].id : null;
    }}

    function currentNode() {{
      const map = currentMap();
      return map.nodes.find(node => node.id === activeNode) || map.nodes[0];
    }}

    function currentAction() {{
      const map = currentMap();
      return ((map.dashboard || {{}}).actions || []).find(action => action.id === activeAction);
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }}[char]));
    }}

    function renderTabs() {{
      const tabs = document.getElementById('tabs');
      tabs.innerHTML = '';
      DATA.maps.forEach(map => {{
        const button = document.createElement('button');
        button.textContent = map.title;
        button.className = map.id === activeMap ? 'active' : '';
        button.addEventListener('click', () => {{
          activeMap = map.id;
          const selectedMap = currentMap();
          activeNode = selectedMap.nodes[0].id;
          activeAction = firstActionId(selectedMap);
          render();
        }});
        tabs.appendChild(button);
      }});
    }}

    function renderDashboardSummary(map, headingHtml) {{
      const dashboard = map.dashboard;
      if (!dashboard || !dashboard.summary) return '';
      const groups = dashboard.document_groups || [];
      const pills = groups.map(group => {{
        const item = dashboard.summary[group.id] || {{
          ready_to_review: 0,
          missing_document: 0,
          needs_researcher_decision: 0,
          total: 0
        }};
        const primary = item.needs_researcher_decision
          ? item.needs_researcher_decision + ' decision'
          : item.ready_to_review + ' ready';
        return `
          <div class="summary-pill">
            <strong>${{escapeHtml(primary)}}</strong>
            <span>${{escapeHtml(group.title)}}</span>
            <span>${{escapeHtml(item.missing_document + ' missing · ' + item.total + ' total')}}</span>
          </div>
        `;
      }}).join('');
      return `
        <div class="section dashboard-summary">
          ${{headingHtml || '<h3>Dashboard Summary</h3>'}}
          <div class="summary-grid">${{pills}}</div>
        </div>
      `;
    }}

    function renderActionQueue() {{
      const map = currentMap();
      const dashboard = map.dashboard || {{}};
      const actions = dashboard.actions || [];
      const queue = document.getElementById('actionQueue');
      if (!actions.length) {{
        queue.innerHTML = `${{renderDashboardSummary(map, '<h2>Dashboard Summary</h2>')}}
          <h2>Action Queue</h2>
          <p class="meta">No researcher-facing actions are recorded for this run.</p>`;
        return;
      }}
      const groups = dashboard.document_groups || [];
      const selectedAction = currentAction() || actions[0];
      queue.innerHTML = `
        ${{renderDashboardSummary(map, '<h2>Dashboard Summary</h2>')}}
        <div class="next-action">Next action: Review ${{escapeHtml(selectedAction.linked_document.label)}}</div>
        <h2>Action Queue</h2>
        <div class="action-help">Select an action to inspect the source document and next command.</div>
        <div class="action-groups">
          ${{groups.map(group => {{
            const groupActions = actions.filter(action => action.priority === group.id);
            return `
              <div class="action-group">
                <div class="action-group-title">${{escapeHtml(group.title)}}</div>
                ${{groupActions.map(action => `
                  <button type="button" class="action-card ${{action.id === activeAction ? 'active' : ''}}" data-action="${{escapeHtml(action.id)}}">
                    <strong>${{escapeHtml(action.linked_document.label)}}</strong>
                    <span>${{escapeHtml(action.status)}}</span>
                  </button>
                `).join('')}}
              </div>
            `;
          }}).join('')}}
        </div>
      `;
      queue.querySelectorAll('[data-action]').forEach(button => {{
        button.addEventListener('click', () => {{
          activeAction = button.dataset.action;
          renderActionQueue();
          renderDetails();
        }});
      }});
    }}

    function renderDiagram() {{
      const map = currentMap();
      const nodesById = Object.fromEntries(map.nodes.map(node => [node.id, node]));
      const edgeMarkup = map.nodes.flatMap(node =>
        (node.edges || []).map(targetId => {{
          const target = nodesById[targetId];
          if (!target) return '';
          const x1 = node.x + 180;
          const y1 = node.y + 45;
          const x2 = target.x;
          const y2 = target.y + 45;
          const mid = (x1 + x2) / 2;
          return `<path class="edge" d="M ${{x1}} ${{y1}} C ${{mid}} ${{y1}}, ${{mid}} ${{y2}}, ${{x2}} ${{y2}}" />`;
        })
      ).join('');

      const nodeMarkup = map.nodes.map(node => `
        <g class="node ${{node.id === activeNode ? 'active' : ''}}" tabindex="0" role="button" aria-label="${{escapeHtml(node.title)}}" data-node="${{escapeHtml(node.id)}}" transform="translate(${{node.x}}, ${{node.y}})">
          <rect width="190" height="92"></rect>
          <text class="phase" x="14" y="24">${{escapeHtml(node.phase)}}</text>
          <text class="title" x="14" y="48">${{escapeHtml(node.title)}}</text>
          <text x="14" y="72" font-size="12">${{escapeHtml(node.summary.slice(0, 28))}}${{node.summary.length > 28 ? '...' : ''}}</text>
        </g>
      `).join('');

      document.getElementById('diagram').innerHTML = `
        <svg viewBox="0 0 1120 620" role="img" aria-label="${{escapeHtml(map.title)}}">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#8c958f"></path>
            </marker>
          </defs>
          ${{edgeMarkup}}
          ${{nodeMarkup}}
        </svg>
      `;
      document.querySelectorAll('.node').forEach(element => {{
        const activate = () => {{
          activeNode = element.dataset.node;
          activeAction = null;
          renderActionQueue();
          renderDiagram();
          renderDetails();
        }};
        element.addEventListener('click', activate);
        element.addEventListener('keydown', event => {{
          if (event.key === 'Enter' || event.key === ' ') {{
            event.preventDefault();
            activate();
          }}
        }});
      }});
    }}

    function renderDetails() {{
      const map = currentMap();
      const action = currentAction();
      if (action) {{
        const doc = action.linked_document || {{}};
        document.getElementById('details').innerHTML = `
          <div class="next-action">Next action: Review ${{escapeHtml((action.linked_document || {{}}).label || 'linked document')}}</div>
          <h2>${{escapeHtml(action.title)}}</h2>
          <div class="meta">${{escapeHtml(action.category)}} / ${{escapeHtml(action.status || 'unknown')}}</div>
          <p>${{escapeHtml(action.why || '')}}</p>
          <div class="section">
            <h3>Linked Document</h3>
            <div class="docs">
              <button type="button" class="file-button" data-path="${{escapeHtml(pathHref(doc.path || ''))}}" data-label="${{escapeHtml(doc.label || 'linked document')}}">${{escapeHtml(doc.label || 'linked document')}}</button>
            </div>
          </div>
          <div class="section">
            <h3>Suggested Next Command</h3>
            <pre class="command-box">${{escapeHtml(action.suggested_command || 'No command recorded.')}}</pre>
          </div>
          <div class="section">
            <h3>Review Rule</h3>
            <p class="meta">This dashboard can point to the source document and next command, but the Markdown record remains the source of truth.</p>
          </div>
          <div class="section">
            <h3>Preview</h3>
            <div class="file-preview" id="filePreview">
              <div class="preview-head">
                <span>Select the linked document to preview it here.</span>
                <a id="rawFileLink" href="#" hidden>Open raw file</a>
              </div>
              <pre id="filePreviewText"></pre>
            </div>
          </div>
        `;
        attachFilePreviewHandlers();
        return;
      }}
      const node = currentNode();
      const links = (node.responsible || []).map(item =>
        `<button type="button" class="file-button" data-path="${{escapeHtml(pathHref(item.path))}}" data-label="${{escapeHtml(item.label)}}">${{escapeHtml(item.label)}}</button>`
      ).join('');
      const metadata = [
        ['Node Type', node.node_type || 'unclassified'],
        ['Link Status', node.link_status || 'unknown'],
        ['Evidence Strength', node.evidence_strength || 'none'],
        ['Claim Ceiling', node.claim_ceiling || 'unsupported'],
        ['Review Owner', node.review_owner || 'unassigned'],
        ['Researcher Checkpoint Marker', node.requires_researcher_review ? 'required' : 'not required']
      ].map(([key, value]) => `
        <div class="result-row">
          <span class="result-key">${{escapeHtml(key)}}</span>
          <span class="result-value">${{escapeHtml(value)}}</span>
        </div>
      `).join('');
      const linkSection = (items, emptyText) => (items || []).length
        ? `<div class="link-grid">${{items.map(item => `
            <div class="link-card">
              <a href="${{escapeHtml(linkHref(item))}}">${{escapeHtml(item.role || item.kind || item.relation || item.path)}}</a>
              <div class="link-meta">${{escapeHtml([
                item.path,
                item.line ? 'line ' + item.line : '',
                item.relation || '',
                item.status || '',
                item.preview ? 'preview: ' + item.preview : ''
              ].filter(Boolean).join(' · '))}}</div>
            </div>
          `).join('')}}</div>`
        : `<p class="meta">${{escapeHtml(emptyText)}}</p>`;
      const checks = (node.checks || []).map(check => `<li>${{escapeHtml(check)}}</li>`).join('');
      const resultEntries = Object.entries(node.result_summary || {{}});
      const resultMarkup = resultEntries.length
        ? resultEntries.map(([key, value]) => `
          <div class="result-row">
            <span class="result-key">${{escapeHtml(key)}}</span>
            <span class="result-value">${{escapeHtml(value)}}</span>
          </div>
        `).join('')
        : '<p class="meta">No compact result summary recorded for this node.</p>';
      const imageMarkup = (node.images || []).length
        ? (node.images || []).map(image => `
          <figure>
            <img class="evidence-image" src="${{escapeHtml(pathHref(image.path))}}" alt="${{escapeHtml(image.label)}} evidence preview">
            <figcaption class="image-caption">${{escapeHtml(image.label)}} · evidence preview, not a standalone claim</figcaption>
          </figure>
        `).join('')
        : '<p class="meta">No figure preview for this node.</p>';
      document.getElementById('details').innerHTML = `
        <h2>${{escapeHtml(node.title)}}</h2>
        <div class="meta">${{escapeHtml(map.title)}} / ${{escapeHtml(node.phase)}}</div>
        <p>${{escapeHtml(node.summary)}}</p>
        ${{renderDashboardSummary(map)}}
        <div class="section">
          <h3>Link State</h3>
          <div class="results">${{metadata}}</div>
        </div>
        <div class="section">
          <h3>Result Summary</h3>
          <div class="results">${{resultMarkup}}</div>
        </div>
        <div class="section">
          <h3>Evidence Images</h3>
          <div class="image-grid">${{imageMarkup}}</div>
        </div>
        <div class="section">
          <h3>Code Links</h3>
          ${{linkSection(node.code_links, 'No code links recorded for this node.')}}
        </div>
        <div class="section">
          <h3>Result Links</h3>
          ${{linkSection(node.result_links, 'No result links recorded for this node.')}}
        </div>
        <div class="section">
          <h3>Interpretation Links</h3>
          ${{linkSection(node.interpretation_links, 'No interpretation links recorded for this node.')}}
        </div>
        <div class="section">
          <h3>Responsible Files</h3>
          <div class="docs">${{links}}</div>
          <div class="file-preview" id="filePreview">
            <div class="preview-head">
              <span>Select a file to preview it here.</span>
              <a id="rawFileLink" href="#" hidden>Open raw file</a>
            </div>
            <pre id="filePreviewText"></pre>
          </div>
        </div>
        <div class="section">
          <h3>Checks</h3>
          <ul>${{checks}}</ul>
        </div>
      `;
      attachFilePreviewHandlers();
    }}

    function attachFilePreviewHandlers() {{
      document.querySelectorAll('.file-button').forEach(button => {{
        button.addEventListener('click', async () => {{
          const previewText = document.getElementById('filePreviewText');
          const rawLink = document.getElementById('rawFileLink');
          const path = button.dataset.path;
          previewText.textContent = 'Loading ' + path + '...';
          rawLink.hidden = false;
          rawLink.href = path;
          rawLink.textContent = 'Open raw file';
          try {{
            const response = await fetch(path);
            if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
            const text = await response.text();
            previewText.textContent = text.slice(0, 8000);
          }} catch (error) {{
            previewText.textContent = 'Could not preview ' + path + ': ' + error.message;
          }}
        }});
      }});
    }}

    function render() {{
      renderTabs();
      renderActionQueue();
      renderDiagram();
      renderDetails();
    }}

    render();
    window.setInterval(() => window.location.reload(), 10000);
  </script>
</body>
</html>
"""
    rendered = template.replace("{{", "{").replace("}}", "}")
    return rendered.replace("__TITLE__", html.escape(title)).replace("__DATA__", data_json)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-paper-logic",
        action="store_true",
        help="Include the paper logic workflow when manuscript planning has been requested.",
    )
    args = parser.parse_args()
    for path in write_outputs(include_paper_logic=args.include_paper_logic):
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        print(f"Generated {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
