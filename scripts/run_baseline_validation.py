#!/usr/bin/env python3
"""Check that the physics research harness has its baseline files in place."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "AGENTS.md",
    "GEMINI.md",
    "PHYSICS.md",
    "README.md",
    "skills/anomaly-debugging/SKILL.md",
    "skills/baseline-validation/SKILL.md",
    "skills/existing-research-onboarding/SKILL.md",
    "skills/harness-evaluation/SKILL.md",
    "skills/literature-review-planning/SKILL.md",
    "skills/model-specification/SKILL.md",
    "skills/dimensional-analysis/SKILL.md",
    "skills/numerical-validation/SKILL.md",
    "skills/claim-to-evidence/SKILL.md",
    "skills/research-plan-review/SKILL.md",
    "skills/research-retrospective/SKILL.md",
    "skills/researcher-review-loop/SKILL.md",
    "skills/scientific-verification-before-claim/SKILL.md",
    "skills/seed-design/SKILL.md",
    "skills/task-intake/SKILL.md",
    "docs/logs/anomaly_log.md",
    "docs/assumptions.md",
    "docs/baseline_registry.md",
    "docs/logs/toy_model_log.md",
    "docs/logs/reproduction_log.md",
    "docs/validation_log.md",
    "docs/workflow_code_map.md",
    "docs/workflow_diagrams.md",
    "workflow_map.html",
    "workflow_map.json",
    "docs/workflow_overview.md",
    "docs/paper_logic_diagram.md",
    "docs/researcher_review_log.md",
    "docs/decision_log.md",
    "docs/adoption/existing_project_intake.md",
    "docs/adoption/existing_results_inventory.md",
    "docs/adoption/retrofit_validation_plan.md",
    "docs/adoption/adoption_log.md",
    "docs/logs/hypothesis_log.md",
    "docs/harness/harness_evaluation_log.md",
    "docs/harness/harness_evaluation_plan.md",
    "docs/harness/harness_evaluation_scenarios.md",
    "docs/harness/harness_pilot_protocol.md",
    "docs/lineage/README.md",
    "docs/lineage/iteration_template.md",
    "docs/logs/negative_results.md",
    "docs/logs/open_questions.md",
    "docs/research_plan.md",
    "docs/research_retrospective.md",
    "docs/research_state.md",
    "docs/logs/tacit_patterns.md",
    "scripts/audit_existing_project.py",
    "scripts/evaluate_harness.py",
    "scripts/generate_workflow_map.py",
    "scripts/validate_workflow_links.py",
]

CODE_DIRS = ["src", "scripts", "notebooks"]
BANNED_MATPLOTLIB_SHOW = "plt." + "show("


def check_required_paths() -> list[str]:
    missing = []
    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).exists():
            missing.append(relative_path)
    return missing


def scan_for_matplotlib_show() -> list[str]:
    matches = []
    for directory in CODE_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in {".py", ".ipynb"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            if BANNED_MATPLOTLIB_SHOW in text:
                matches.append(str(path.relative_to(ROOT)))
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the baseline structure of the physics research harness."
    )
    parser.add_argument(
        "--skip-plt-scan",
        action="store_true",
        help="Only check required harness paths.",
    )
    args = parser.parse_args()

    missing = check_required_paths()
    plt_matches = [] if args.skip_plt_scan else scan_for_matplotlib_show()

    if missing:
        print("Missing required harness files:")
        for path in missing:
            print(f"  - {path}")

    if plt_matches:
        print(f"Found prohibited {BANNED_MATPLOTLIB_SHOW}) usage:")
        for path in plt_matches:
            print(f"  - {path}")

    if missing or plt_matches:
        return 1

    print("Baseline harness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
