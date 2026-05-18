#!/usr/bin/env python3
"""Claude Code hook entry point for live workflow diagram updates.

Registered in .claude/settings.local.json under PreToolUse and PostToolUse
for the Agent tool. Reads the Claude Code hook JSON from stdin, extracts the
task description, and updates live_workflow_diagram.md.

Exit code 0 always — warnings go to stderr but the tool call is never blocked.
(Enforcement is through PHYSICS.md rules, not hard blocking.)

Usage (set in .claude/settings.local.json):
    python scripts/workflow_hooks.py pre
    python scripts/workflow_hooks.py post
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_workflow_diagram as uwd  # noqa: E402


AGENT_NAME = "lead-agent"
MAX_STEP_LEN = 100

# Signal artifacts whose Write/Edit should produce a Cartographer event.
# Maps relative path (within a run dir) -> (event label, optional gate name,
# optional gate status). When `gate` is None, only an event-log line is added.
SIGNAL_ARTIFACTS = {
    "docs/orient_note.md":             ("Orient note recorded",          "Professor interview", "pending"),
    "docs/interview_notes.md":         ("Interview notes recorded",      "Professor interview", "pass"),
    "docs/literature_review_plan.md":  ("Literature review plan recorded","Literature review and replanning", "pass"),
    "docs/model_spec.md":              ("Model spec recorded",            None, None),
    "docs/baseline_strategy.md":       ("Baseline strategy decided",      "Baseline or reproduction target", "pass"),
    "docs/research_plan.md":           ("Research plan updated",          None, None),
    "docs/replanning_memo.md":         ("Replanning memo updated",        None, None),
    "docs/gates/agent_spawn_log.md":   ("Agent spawn log updated",        None, None),
    "docs/gates/validation_log.md":    ("Validation log updated",         "Execution", "in_progress"),
    "docs/research_retrospective.md":  ("Retrospective recorded",         "Completion conference", "pass"),
}


FIGURE_EXTS = (".png", ".pdf", ".svg", ".jpg", ".jpeg")
CACHE_EXTS = (".npy", ".npz", ".pkl", ".pickle", ".joblib")


def signal_for(file_path_str: str):
    """Return (event, gate, gate_status, run_dir) if path matches a signal artifact."""
    if not file_path_str:
        return None
    p = Path(file_path_str).resolve()
    parts = list(p.parts)
    for i, part in enumerate(parts):
        if part.lower() == "researchpartner-runs" and i + 1 < len(parts):
            run_dir = Path(*parts[: i + 2])
            try:
                rel = p.relative_to(run_dir).as_posix()
            except ValueError:
                return None
            # docs/checkpoints/stage_N_checkpoint.md is a stage-advance signal
            if rel.startswith("docs/checkpoints/stage_") and rel.endswith("_checkpoint.md"):
                return ("Stage checkpoint written", "Completion conference", "pass", run_dir)
            # docs/meetings/YYYY-MM-DD-*.md is a meeting record signal
            if rel.startswith("docs/meetings/") and rel.endswith(".md"):
                return (f"Meeting recorded ({Path(rel).stem})", None, None, run_dir)
            # outputs/figures/*.png|pdf|svg|jpg → "Figure generated"
            if rel.startswith("outputs/figures/") and rel.lower().endswith(FIGURE_EXTS):
                return (f"Figure generated ({Path(rel).name})", "Visualization", "in_progress", run_dir)
            # errors/*.err → "Error file created" (negative signal — does NOT advance any gate)
            if rel.startswith("errors/") and rel.endswith(".err"):
                return (f"Error file created ({Path(rel).name})", None, None, run_dir)
            # cache/*.npy|npz|pkl|pickle|joblib → "Cache artifact written"
            if rel.startswith("cache/") and rel.lower().endswith(CACHE_EXTS):
                return (f"Cache artifact written ({Path(rel).name})", None, None, run_dir)
            # docs/model_versions/<id>.md → new model_version lineage node
            if rel.startswith("docs/model_versions/") and rel.endswith(".md"):
                return (f"Model version recorded ({Path(rel).stem})", None, None, run_dir)
            # literature/reviews/<paper_id>.md → paper lineage node
            if rel.startswith("literature/reviews/") and rel.endswith(".md"):
                return (f"Paper review recorded ({Path(rel).stem})", None, None, run_dir)
            # docs/claims/<claim_id>.md → claim lineage node
            if rel.startswith("docs/claims/") and rel.endswith(".md"):
                return (f"Claim recorded ({Path(rel).stem})", None, None, run_dir)
            if rel in SIGNAL_ARTIFACTS:
                ev, gate, gs = SIGNAL_ARTIFACTS[rel]
                return (ev, gate, gs, run_dir)
            return None
    return None


def run_artifact_event(tool_name: str, file_path_str: str, phase: str) -> None:
    """Record a Cartographer event for Write/Edit of a signal artifact."""
    sig = signal_for(file_path_str)
    if sig is None:
        return
    event_label, gate, gate_status, run_dir = sig
    diagram_path = run_dir / "docs" / "live_workflow_diagram.md"
    if not diagram_path.exists():
        # Fall back to auto-discovery in case the run uses a non-standard location
        diagram_path = uwd.find_active_diagram()
        if diagram_path is None:
            return
    try:
        content = diagram_path.read_text(encoding="utf-8")
        event = "complete" if phase == "post" else "in_progress"
        content = uwd.append_event(content, event, event_label, AGENT_NAME)
        if phase == "post" and gate and gate_status:
            content = uwd.update_gate_status(content, gate, gate_status)
        diagram_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"WORKFLOW WARNING: artifact event failed: {exc}", file=sys.stderr)


def extract_step(tool_input: dict) -> str:
    """Pull the most descriptive string out of an Agent tool_input dict."""
    step = (
        tool_input.get("description")
        or tool_input.get("prompt", "")[:MAX_STEP_LEN]
        or "unnamed task"
    )
    if isinstance(step, str):
        return step[:MAX_STEP_LEN]
    return "unnamed task"


def run_pre(tool_input: dict) -> None:
    step = extract_step(tool_input)
    diagram_path = uwd.find_active_diagram()

    if diagram_path is None:
        print(
            "WORKFLOW WARNING: No live_workflow_diagram.md found in any ResearchPartner-runs "
            "directory. If this is a research task, run scripts/start_research_run.py first.",
            file=sys.stderr,
        )
        return

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = uwd.update_active_step(content, step, AGENT_NAME)
        content = uwd.append_event(content, "start", step, AGENT_NAME)
        diagram_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"WORKFLOW WARNING: Could not update diagram (pre): {exc}", file=sys.stderr)


def run_post(tool_input: dict) -> None:
    step = extract_step(tool_input)
    diagram_path = uwd.find_active_diagram()

    if diagram_path is None:
        return

    try:
        content = diagram_path.read_text(encoding="utf-8")
        content = uwd.append_event(content, "complete", step, AGENT_NAME)
        diagram_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"WORKFLOW WARNING: Could not update diagram (post): {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("pre", "post"):
        print("Usage: workflow_hooks.py <pre|post>", file=sys.stderr)
        return 0  # Never block on bad invocation

    phase = sys.argv[1]

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # Never block on parse failure

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name == "Agent":
        if phase == "pre":
            run_pre(tool_input)
        else:
            run_post(tool_input)
        return 0

    if tool_name in ("Write", "Edit"):
        file_path_str = tool_input.get("file_path", "")
        run_artifact_event(tool_name, file_path_str, phase)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
