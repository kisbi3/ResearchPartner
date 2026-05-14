#!/usr/bin/env python3
"""Evaluate whether the physics research harness covers realistic scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Scenario:
    name: str
    skills: tuple[str, ...]
    docs: tuple[str, ...]
    rule_terms: tuple[str, ...]


SCENARIOS = [
    Scenario(
        name="pre_run_workflow_navigation",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/literature-review-planning/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
            "docs/paper_logic_diagram.md",
            "docs/workflow_map.json",
            "docs/workflow_map.html",
            "docs/workflow_code_map.md",
        ),
        rule_terms=("Workflow Visualization", "workflow_map.html", "paper_logic_diagram"),
    ),
    Scenario(
        name="literature_replanning_loop",
        skills=(
            "skills/literature-review-planning/SKILL.md",
            "skills/research-plan-review/SKILL.md",
            "skills/claim-to-evidence/SKILL.md",
        ),
        docs=(
            "docs/literature/README.md",
            "docs/literature/paper_request_queue.md",
            "docs/literature/literature_review_template.md",
            "docs/literature/replanning_memo_template.md",
            "docs/run_templates/research_run_packet_template.md",
        ),
        rule_terms=(
            "Literature Replanning Hook",
            "Literature Replanning Loop",
            "researcher-provided PDFs",
            "literature/pdfs/",
            "novelty map",
            "reproduction targets",
        ),
    ),
    Scenario(
        name="live_workflow_diagram_agent",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/baseline-validation/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
            "docs/run_templates/live_workflow_diagram_template.md",
            "docs/research_plan.md",
            "docs/validation_log.md",
            "docs/researcher_review_log.md",
        ),
        rule_terms=(
            "scripts/start_research_run.py",
            "Diagram/Cartographer Agent",
            "does not give project opinions",
            "listens to the Professor Orchestrator",
            "live workflow artifact",
            "active step",
            "gates",
            "evidence links",
            "must not strengthen scientific claims",
        ),
    ),
    Scenario(
        name="professor_orchestration",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
            "docs/research_plan.md",
            "docs/decision_log.md",
        ),
        rule_terms=(
            "Professor Orchestrator",
            "Socratic Interviewer",
            "Ontologist",
            "Seed Architect",
            "Evaluator",
            "Contrarian",
            "Hacker",
            "Simplifier",
            "Researcher",
            "Architect",
        ),
    ),
    Scenario(
        name="graduate_test_design_agents",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/baseline-validation/SKILL.md",
            "skills/numerical-validation/SKILL.md",
        ),
        docs=(
            "docs/research_plan.md",
            "docs/baseline_registry.md",
            "docs/validation_log.md",
        ),
        rule_terms=(
            "Graduate Test-Design Agents",
            "interview the professor",
            "interview coding subagents",
            "observables",
            "failure criteria",
        ),
    ),
    Scenario(
        name="coding_subagent_claim_discipline",
        skills=(
            "skills/numerical-validation/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/validation_log.md",
            "docs/decision_log.md",
        ),
        rule_terms=(
            "Coding Subagents",
            "bounded implementation",
            "should not decide",
            "stronger scientific claim",
        ),
    ),
    Scenario(
        name="completion_conference_reporting",
        skills=(
            "skills/researcher-review-loop/SKILL.md",
            "skills/research-retrospective/SKILL.md",
        ),
        docs=(
            "docs/researcher_review_log.md",
            "docs/research_retrospective.md",
            "docs/research_state.md",
            "docs/run_templates/research_run_packet_template.md",
        ),
        rule_terms=(
            "completion conference",
            "all agents",
            "visualization materials",
            "report to the user",
        ),
    ),
    Scenario(
        name="hook_aware_scientific_loop",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/model-specification/SKILL.md",
            "skills/baseline-validation/SKILL.md",
            "skills/numerical-validation/SKILL.md",
        ),
        docs=(
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
            "docs/research_plan.md",
            "docs/baseline_registry.md",
            "docs/validation_log.md",
        ),
        rule_terms=(
            "Task Intake Hook",
            "Ambiguity Hook",
            "Assumption/Units Hook",
            "Baseline Gate Hook",
            "Graduate Test-Design Hook",
            "Code-before-Test Hook",
            "Numerical Stability Hook",
            "Waiver Hook",
        ),
    ),
    Scenario(
        name="provenance_and_reproducibility_hooks",
        skills=(
            "skills/numerical-validation/SKILL.md",
            "skills/dimensional-analysis/SKILL.md",
            "skills/research-retrospective/SKILL.md",
        ),
        docs=(
            "docs/validation_log.md",
            "docs/logs/negative_results.md",
            "docs/research_retrospective.md",
        ),
        rule_terms=(
            "Parameter Change Hook",
            "Randomness/Reproducibility Hook",
            "Data Lineage Hook",
            "Figure Provenance Hook",
            "Unit Conversion Hook",
            "Environment Capture Hook",
        ),
    ),
    Scenario(
        name="manuscript_and_artifact_drift_hooks",
        skills=(
            "skills/scientific-verification-before-claim/SKILL.md",
            "skills/claim-to-evidence/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
        ),
        docs=(
            "docs/decision_log.md",
            "docs/researcher_review_log.md",
            "docs/logs/open_questions.md",
        ),
        rule_terms=(
            "Claim Strength Hook",
            "Literature Claim Hook",
            "Manuscript Drift Hook",
            "Artifact Freshness Hook",
            "Scope Creep Hook",
            "Reviewer Simulation Hook",
            "Negative Result Hook",
            "Cartographer Hook",
            "Retrospective Hook",
        ),
    ),
    Scenario(
        name="live_linked_research_graph",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/numerical-validation/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
            "docs/run_templates/cartographer_update_template.md",
            "docs/run_templates/live_workflow_diagram_template.md",
            "docs/run_templates/research_run_packet_template.md",
        ),
        rule_terms=(
            "Live Linked Research Graph",
            "Code links",
            "Result links",
            "Interpretation links",
            "Link Status",
            "Evidence Strength",
            "Claim ceiling",
            "Researcher Checkpoint Marker",
            "Artifact Preview",
            "Staleness propagation",
        ),
    ),
    Scenario(
        name="new_model_without_baseline",
        skills=(
            "skills/research-plan-review/SKILL.md",
            "skills/model-specification/SKILL.md",
            "skills/baseline-validation/SKILL.md",
            "skills/numerical-validation/SKILL.md",
        ),
        docs=(
            "docs/research_plan.md",
            "docs/baseline_registry.md",
            "docs/validation_log.md",
        ),
        rule_terms=("baseline", "full-scale", "claim-to-evidence"),
    ),
    Scenario(
        name="existing_project_with_old_figures",
        skills=(
            "skills/existing-research-onboarding/SKILL.md",
            "skills/claim-to-evidence/SKILL.md",
            "skills/baseline-validation/SKILL.md",
        ),
        docs=(
            "docs/adoption/existing_project_intake.md",
            "docs/adoption/existing_results_inventory.md",
            "docs/adoption/retrofit_validation_plan.md",
            "docs/adoption/adoption_log.md",
        ),
        rule_terms=("existing research", "inventory", "retrofit"),
    ),
    Scenario(
        name="manuscript_overclaim",
        skills=(
            "skills/scientific-verification-before-claim/SKILL.md",
            "skills/claim-to-evidence/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
        ),
        docs=(
            "docs/decision_log.md",
            "docs/researcher_review_log.md",
        ),
        rule_terms=("No scientific claim", "weakest", "evidence"),
    ),
    Scenario(
        name="anomalous_simulation",
        skills=(
            "skills/anomaly-debugging/SKILL.md",
            "skills/numerical-validation/SKILL.md",
            "skills/dimensional-analysis/SKILL.md",
        ),
        docs=(
            "docs/logs/anomaly_log.md",
            "docs/logs/negative_results.md",
            "docs/validation_log.md",
        ),
        rule_terms=("anomaly", "classify", "expected behavior"),
    ),
    Scenario(
        name="numerical_code_change",
        skills=(
            "skills/numerical-validation/SKILL.md",
            "skills/baseline-validation/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/validation_log.md",
            "docs/baseline_registry.md",
            "docs/decision_log.md",
        ),
        rule_terms=("integration schemes", "visual agreement", "validation"),
    ),
    Scenario(
        name="end_of_iteration_retrospective",
        skills=(
            "skills/research-retrospective/SKILL.md",
            "skills/researcher-review-loop/SKILL.md",
        ),
        docs=(
            "docs/research_retrospective.md",
            "docs/research_state.md",
            "docs/logs/hypothesis_log.md",
            "docs/lineage/README.md",
            "docs/logs/open_questions.md",
        ),
        rule_terms=("Every research iteration", "reusable artifact", "lineage"),
    ),
]


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def harness_rule_text() -> str:
    files = ["AGENTS.md", "GEMINI.md", "PHYSICS.md", "README.md"]
    return "\n".join(read_text(path) for path in files)


def evaluate_scenario(scenario: Scenario, rule_text: str) -> dict[str, object]:
    missing_skills = [path for path in scenario.skills if not (ROOT / path).exists()]
    missing_docs = [path for path in scenario.docs if not (ROOT / path).exists()]
    missing_terms = [
        term for term in scenario.rule_terms if term.lower() not in rule_text.lower()
    ]

    total = len(scenario.skills) + len(scenario.docs) + len(scenario.rule_terms)
    missing = len(missing_skills) + len(missing_docs) + len(missing_terms)
    score = 100 if total == 0 else round(100 * (total - missing) / total)

    if missing == 0:
        status = "pass"
    elif score >= 75:
        status = "partial"
    else:
        status = "fail"

    return {
        "name": scenario.name,
        "status": status,
        "score": score,
        "missing_skills": missing_skills,
        "missing_docs": missing_docs,
        "missing_rule_terms": missing_terms,
    }


def format_report(results: list[dict[str, object]]) -> str:
    passing = sum(1 for result in results if result["status"] == "pass")
    partial = sum(1 for result in results if result["status"] == "partial")
    failing = sum(1 for result in results if result["status"] == "fail")
    average = round(sum(int(result["score"]) for result in results) / len(results))

    lines = [
        "# Harness Evaluation Report",
        "",
        f"- Scenarios: {len(results)}",
        f"- Pass: {passing}",
        f"- Partial: {partial}",
        f"- Fail: {failing}",
        f"- Average score: {average}",
        "",
        "| Scenario | Status | Score | Gaps |",
        "|---|---|---:|---|",
    ]

    for result in results:
        gaps = []
        for key, label in (
            ("missing_skills", "skills"),
            ("missing_docs", "docs"),
            ("missing_rule_terms", "rules"),
        ):
            values = result[key]
            if values:
                gaps.append(f"{label}: {', '.join(values)}")
        gap_text = "; ".join(gaps) if gaps else "none"
        lines.append(
            f"| {result['name']} | {result['status']} | {result['score']} | {gap_text} |"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate harness coverage against realistic physics research scenarios."
    )
    parser.add_argument(
        "--output",
        help="Optional markdown output path. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--fail-on-partial",
        action="store_true",
        help="Return non-zero if any scenario is partial.",
    )
    args = parser.parse_args()

    rule_text = harness_rule_text()
    results = [evaluate_scenario(scenario, rule_text) for scenario in SCENARIOS]
    report = format_report(results)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)

    has_failures = any(result["status"] == "fail" for result in results)
    has_partials = any(result["status"] == "partial" for result in results)
    if has_failures or (args.fail_on_partial and has_partials):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
