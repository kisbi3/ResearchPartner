#!/usr/bin/env python3
"""PreToolUse hook: enforce gate sequence before agent spawns.

When the Lead Agent tries to spawn a sub-agent for a step that has
prerequisite gates, this hook checks those gates are recorded.  If any
prerequisite artifact is missing or still contains only template/placeholder
content, the spawn is blocked (exit 2) with a clear fix message.

Covered gate sequence (linear order):
    orient → interview → literature → seed/stage-1 → implementation

The hook detects the intended step from the Agent spawn description + prompt
rather than relying on active_step, so it works even when
update_workflow_diagram.py has not been called yet.

The critical rule this enforces:
    Writing content in your response text is NOT sufficient.
    Gate artifacts MUST be saved via the Write tool so the hook can detect them.

Exit codes:
    0  allow the spawn (prerequisites satisfied, or step not recognised)
    2  block the spawn (prerequisite gate not recorded)

Bypass: set RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE=1 for an explicit one-off
waiver (logged to stderr).
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402


# ── Gate check modules (in required sequence order) ───────────────────────────
# Each entry is (logical_step_name, check_module_name).
# The check module must expose check_project(project: Path) → (int, list[str]).

GATE_CHECKS: list[tuple[str, str]] = [
    ("orient",            "check_orient_recorded"),
    ("interview",         "check_interview_recorded"),
    ("literature",        "check_literature_reviewed"),
    ("model",             "check_model_specified"),
    ("baseline_strategy", "check_baseline_strategy"),
    ("baseline",          "check_baseline_gate"),
    ("validation_recent", "check_validation_recent"),
    ("review_recent",     "check_researcher_review_recent"),
]

# Human-readable labels and artifact paths for block messages.
GATE_LABELS: dict[str, str] = {
    "orient":            "Orient gate",
    "interview":         "Interview gate",
    "literature":        "Literature gate",
    "model":             "Model specification gate",
    "baseline_strategy": "Baseline strategy gate",
    "baseline":          "Baseline gate",
    "validation_recent": "Recent validation gate",
    "review_recent":     "Recent researcher-review gate",
}
GATE_ARTIFACTS: dict[str, str] = {
    "orient":            "docs/gates/orient_note.md",
    "interview":         "docs/gates/interview_notes.md",
    "literature":        "docs/literature/literature_review_plan.md",
    "model":             "docs/plan/model_spec.md",
    "baseline_strategy": "docs/plan/baseline_strategy.md",
    "baseline":          "docs/gates/baseline_registry.md",
    "validation_recent": "docs/gates/validation_log.md",
    "review_recent":     "docs/process/researcher_review_log.md",
}


# ── Skill → prerequisite gate mapping ────────────────────────────────────────
# Keys are logical skill names (for readability only).
# "patterns" match against the combined Agent description + prompt text.
# "requires" lists the gate steps that must pass before this skill may spawn.

SKILL_REQUIREMENTS: list[dict] = [
    {
        "skill": "professor-interview",
        "patterns": [
            r"professor[-_\s]?interview",
            r"skills/professor-interview",
            r"skills/interview",
            r"\binterview\s+gate\b",
            r"crystallized\s+research\s+question",
        ],
        "requires": ["orient"],
    },
    {
        "skill": "literature-review-planning",
        "patterns": [
            r"literature[-_\s]?review[-_\s]?planning",
            r"skills/literature",
            r"\bpaper[-_\s]?request\b",
            r"\breplanning\b",
            r"\bliterature\s+gate\b",
        ],
        "requires": ["orient", "interview"],
    },
    {
        "skill": "seed-design",
        "patterns": [
            r"seed[-_\s]?design",
            r"test[-_\s]?design[-_\s]?seed",
            r"\bstage[-_\s]?1\b",
            r"skills/seed",
            r"synthetic\s+data\s+generation",
            r"\bseed\s+stage\b",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline_strategy"],
    },
    {
        "skill": "implementation-agent",
        "patterns": [
            r"implementation[-_\s]?agent",
            r"skills/implementation",
            r"\bcoding\s+agent\b",
            r"spawning\s+implementation",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline_strategy"],
    },
    {
        "skill": "model-specification",
        "patterns": [
            r"model[-_\s]?spec",
            r"skills/model-spec",
            r"\bmodel\s+specification\b",
        ],
        "requires": ["orient", "interview", "literature"],
    },
    {
        "skill": "baseline-strategy",
        "patterns": [
            r"baseline[-_\s]?strateg",
            r"skills/baseline[-_\s]?strateg",
            r"\bbaseline\s+plan\b",
            r"\btoy\s+model\s+plan\b",
        ],
        "requires": ["orient", "interview", "literature", "model"],
    },
    {
        "skill": "scientific-validator",
        "patterns": [
            r"scientific[-_\s]?verif",
            r"skills/scientific[-_\s]?verif",
            r"\bvalidat",
            r"numerical[-_\s]?validation",
            r"skills/numerical[-_\s]?validation",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline_strategy", "baseline"],
    },
    {
        "skill": "claim-to-evidence",
        "patterns": [
            r"claim[-_\s]?to[-_\s]?evidence",
            r"skills/claim[-_\s]?to[-_\s]?evidence",
            r"\bclaim\s+ceiling\b",
            r"\bpromote\s+claim\b",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline_strategy",
                     "baseline", "validation_recent", "review_recent"],
    },
    {
        "skill": "research-retrospective",
        "patterns": [
            r"retrospective",
            r"skills/research[-_\s]?retrospective",
            r"\bcompletion\s+conference\b",
            r"\bwrap[-_\s]?up\b",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline_strategy",
                     "baseline", "review_recent"],
    },
    {
        "skill": "numerical-validation",
        "patterns": [
            r"skills/numerical[-_\s]?validation",
            r"\bnumerical\s+check\b",
            r"\bconservation\s+check\b",
            r"\bdimensional\s+analysis\b",
            r"skills/dimensional[-_\s]?analysis",
        ],
        "requires": ["orient", "interview", "literature", "model", "baseline"],
    },
]


def detect_required_gates(text: str) -> tuple[str, list[str]]:
    """Return (skill_name, required_gate_steps) for the first matching skill.

    Returns ("", []) when no skill pattern matches — meaning the spawn is
    not recognised as a gated step and is allowed through.
    """
    for entry in SKILL_REQUIREMENTS:
        for pattern in entry["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return entry["skill"], entry["requires"]
    return "", []


def run_gate_check(project: Path, step: str) -> tuple[int, list[str]]:
    """Import and run the check module for the given gate step.

    Returns (0, [...]) when the gate passes or when no check module exists
    for the step (unknown steps are treated as passed so the hook stays
    forward-compatible with gates added later without a check script yet).
    """
    for gate_step, module_name in GATE_CHECKS:
        if gate_step == step:
            try:
                mod = importlib.import_module(module_name)
            except ImportError as exc:
                # Check script missing from scripts/ — don't block, just warn.
                return 1, [f"Could not import {module_name}: {exc}"]
            try:
                return mod.check_project(project)
            except Exception as exc:
                return 1, [f"Error running {module_name}.check_project(): {exc}"]
    # No matching check module — step treated as passed.
    return 0, []


def main() -> int:
    # ── Read hook payload from stdin ──────────────────────────────────────────
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # Malformed input — don't block

    if payload.get("tool_name") != "Agent":
        return 0

    # ── Bypass via environment variable ───────────────────────────────────────
    if os.environ.get("RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE") == "1":
        print(
            "GATE-SEQUENCE BYPASS: spawn allowed via "
            "RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE=1",
            file=sys.stderr,
        )
        return 0

    # ── Extract spawn description + prompt ────────────────────────────────────
    tool_input = payload.get("tool_input", {}) or {}
    description = tool_input.get("description", "") or ""
    prompt = tool_input.get("prompt", "") or ""
    combined = f"{description}\n{prompt}"

    skill_name, required_gates = detect_required_gates(combined)
    if not required_gates:
        return 0  # Not a gated spawn — let through

    # ── Locate project root ───────────────────────────────────────────────────
    try:
        project = project_root_mod.resolve_project(None, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return 0  # Not inside a research project — don't block

    # ── Check prerequisites in order ──────────────────────────────────────────
    failures: list[tuple[str, list[str]]] = []
    for step in required_gates:
        code, messages = run_gate_check(project, step)
        if code != 0:
            failures.append((step, messages))

    if not failures:
        return 0  # All prerequisites satisfied

    # ── Block with a clear fix message ────────────────────────────────────────
    step, messages = failures[0]
    gate_label   = GATE_LABELS.get(step, step)
    artifact_path = GATE_ARTIFACTS.get(step, f"(see docs/gates/{step}_note.md)")
    fail_detail  = messages[0] if messages else "gate artifact not recorded"

    print(
        f"GATE SEQUENCE BLOCK: cannot spawn '{skill_name}' agent — "
        f"{gate_label} not complete.\n"
        f"\n"
        f"  Problem : {fail_detail}\n"
        f"  Artifact: {artifact_path}\n"
        f"\n"
        f"  Rule: writing skill output in your response text is NOT sufficient.\n"
        f"        The gate artifact must be saved with the Write tool so that\n"
        f"        the workflow hooks can detect and record it.\n"
        f"\n"
        f"  Fix: use the Write tool to write the complete skill output to\n"
        f"       {artifact_path}, then retry the agent spawn.\n"
        f"\n"
        f"  Bypass: set RESEARCH_HARNESS_BYPASS_GATE_SEQUENCE=1 for an\n"
        f"          explicit one-off waiver (logged to stderr).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
