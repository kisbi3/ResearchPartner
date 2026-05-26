#!/usr/bin/env python3
"""Evaluate whether the physics research harness covers realistic scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import contextlib
import importlib.util
import io
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Scenario:
    name: str
    skills: tuple[str, ...]
    docs: tuple[str, ...]
    rule_terms: tuple[str, ...]
    checks: tuple[str, ...] = ()


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
            "workflow_map.json",
            "workflow_map.html",
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
            "docs/literature/paper_review_index_template.md",
            "docs/literature/literature_review_template.md",
            "docs/literature/replanning_memo_template.md",
            "docs/run_templates/research_run_packet_template.md",
            "scripts/scaffold_paper_review.py",
            "scripts/extract_paper_text.py",
            "scripts/draft_paper_review.py",
            "scripts/process_paper_for_review.py",
            "scripts/check_paper_review_quality.py",
        ),
        rule_terms=(
            "Literature Replanning Hook",
            "Literature Replanning Loop",
            "researcher-provided PDFs",
            "literature/pdfs/",
            "novelty map",
            "reproduction targets",
            "section-by-section paper review",
            "Figure/Table-by-Figure/Table Review",
            "PDF text extraction is a reading aid",
            "Machine-Assisted Draft From Extracted Text",
            "process_paper_for_review.py",
            "clickable links across the literature graph",
            "check_paper_review_quality.py",
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
            "scripts/init_research_project.py",
            "workflow_hooks.py (hook-driven, not spawned)",
            "does not give project opinions",
            "listens to the Lead Agent",
            "live workflow artifact",
            "active step",
            "gates",
            "evidence links",
            "must not strengthen scientific claims",
        ),
    ),
    Scenario(
        name="live_workflow_map_scaffold_integration",
        skills=("skills/sync-workflow/SKILL.md",),
        docs=(
            "scripts/init_research_project.py",
            "scripts/sync_workflow.py",
            "docs/workflow_overview.md",
        ),
        rule_terms=(
            "docs\\process\\live_workflow_diagram.md",
            "sync_workflow.py",
            "sync",
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
            "Lead Agent",
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
            "Graduate Student role",
            "Lead-loaded task orchestration",
            "leaf Coding Subagents",
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
            "leaf Coding Subagents",
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
            "Graduate Student Role Hook",
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
            "Workflow State Hook",
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
        name="finding_lifecycle_claim_promotion",
        skills=(
            "skills/claim-to-evidence/SKILL.md",
            "skills/anomaly-debugging/SKILL.md",
            "skills/peer-review-professor/SKILL.md",
            "skills/scientific-verification-before-claim/SKILL.md",
        ),
        docs=(
            "docs/harness/finding_lifecycle.md",
            "docs/run_templates/finding_lifecycle_template.md",
            "scripts/check_claim_promotion.py",
            "scripts/check_claim_promotion_freshness.py",
        ),
        rule_terms=(
            "Finding Lifecycle Hook",
            "Evidence Paths Read Directly",
            "candidate findings cannot promote",
            "checker validates only declared structure",
            "confidence threshold is reviewer surface guidance",
        ),
        checks=("check_claim_promotion_lifecycle",),
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
    Scenario(
        name="user_facing_documentation_drift",
        skills=("skills/harness-evaluation/SKILL.md",),
        docs=("README.md", "README.ko.md"),
        rule_terms=(
            "materially change a harness feature",
            "README.md",
            "README.ko.md",
            "same checkpoint",
        ),
    ),
    Scenario(
        name="task_intake_orient_phase",
        skills=("skills/task-intake/SKILL.md",),
        docs=("docs/workflow_overview.md",),
        rule_terms=(
            "skills/task-intake/SKILL.md",
            "Task Intake Hook",
            "first professor question",
            "Orient phase",
            "assigns research roles",
        ),
    ),
    Scenario(
        name="interview_gate_enforcement",
        skills=("skills/professor-interview/SKILL.md",),
        docs=(
            "docs/run_templates/interview_notes_template.md",
            "docs/run_templates/live_workflow_diagram_template.md",
            "docs/workflow_overview.md",
            "docs/workflow_diagrams.md",
        ),
        rule_terms=(
            "Interview Gate Hook",
            "check_interview_recorded.py",
            "docs/gates/interview_notes.md",
            "before Seed or Execute work begins",
            "crystallized research question",
        ),
    ),
    Scenario(
        name="seed_design_graduate_tasks",
        skills=(
            "skills/seed-design/SKILL.md",
            "skills/research-plan-review/SKILL.md",
        ),
        docs=("docs/research_plan.md",),
        rule_terms=(
            "skills/seed-design/SKILL.md",
            "Graduate Student Role Hook",
            "Lead-managed seed task packets",
            "pass/fail criteria",
            "Seed phase",
        ),
    ),
    Scenario(
        name="sync_workflow_lineage_frontmatter",
        skills=("skills/sync-workflow/SKILL.md",),
        docs=("scripts/sync_workflow.py",),
        rule_terms=(
            "skills/sync-workflow/SKILL.md",
            "lineage:",
            "front-matter",
            "/sync-workflow",
        ),
    ),
    Scenario(
        name="multi_agent_spawn_protocol",
        skills=(
            "skills/graduate-student/SKILL.md",
            "skills/implementation-agent/SKILL.md",
            "skills/scientific-validator/SKILL.md",
            "skills/cache-log-auditor/SKILL.md",
            "skills/seed-design/SKILL.md",
        ),
        docs=(
            "scripts/_layout.py",
            "scripts/run_with_capture.py",
            "scripts/audit_run_outputs.py",
        ),
        rule_terms=(
            "Agent Spawning Protocol",
            "Single-Spawner Hierarchy",
            "Parallel Task Coordination Rule",
            "One seed task = one Lead-managed Graduate Student role pass",
            "Graduate Student is not a subagent type",
            "Cache-Log Auditor",
            "Cross-Tier Prohibition",
        ),
    ),
    Scenario(
        name="session_resumption_after_interruption",
        skills=(
            "skills/sync-workflow/SKILL.md",
        ),
        docs=(
            "scripts/check_session_resumable.py",
            "scripts/workflow_hooks.py",
            "docs/run_templates/live_workflow_diagram_template.md",
        ),
        rule_terms=(
            "Session Resumption Hook",
            "check_session_resumable.py",
            "In-Flight Tasks",
            "spawned",
            "acknowledged",
            "abandoned",
        ),
    ),
    Scenario(
        name="computation_checkpoint_resumption",
        skills=(
            "skills/implementation-agent/SKILL.md",
        ),
        docs=(
            "scripts/run_with_checkpoint.py",
            "scripts/check_computation_resumable.py",
        ),
        rule_terms=(
            "Computation Checkpoint Hook",
            "CheckpointManager",
            "check_computation_resumable.py",
            "run_with_checkpoint.py",
            "cache/checkpoint_",
            "orphaned",
        ),
    ),
    Scenario(
        name="capability_manifest_and_hook_registry",
        skills=(
            "skills/harness-evaluation/SKILL.md",
        ),
        docs=(
            "docs/harness/capability_manifest.json",
            "scripts/check_harness_manifest.py",
            "docs/harness/claude_code_unified_implementation_plan.md",
        ),
        rule_terms=(
            "Capability Manifest Hook",
            "check_harness_manifest.py",
            "hook registry",
            "workflow_gate_keys",
            "$CLAUDE_PROJECT_DIR",
        ),
        checks=("check_harness_manifest",),
    ),
    Scenario(
        name="spawn_contracts_and_agent_definitions",
        skills=(
            "skills/harness-evaluation/SKILL.md",
        ),
        docs=(
            "docs/harness/spawn_contracts.json",
            "scripts/check_spawn_contracts.py",
            ".claude/agents/implementation-agent.md",
            ".claude/agents/scientific-validator.md",
            ".claude/agents/cache-log-auditor.md",
            ".claude/agents/peer-review-professor.md",
            "docs/orchestration_protocol.md",
        ),
        rule_terms=(
            "Spawn Contract Consistency Gate",
            "check_spawn_contracts.py",
            "single-spawner model",
            "subagent_type",
            "Agent tool is reserved for the Lead Agent",
            "Explicitly spawned only",
        ),
        checks=("check_spawn_contracts",),
    ),
    Scenario(
        name="ci_enforcement",
        skills=(
            "skills/harness-evaluation/SKILL.md",
        ),
        docs=(
            ".github/workflows/harness-checks.yml",
            "docs/hooks_reference.md",
            "docs/harness/capability_manifest.json",
        ),
        rule_terms=(
            "CI Enforcement Gate",
            "repo-state checker",
            "does not replace live Claude Code hook firing",
        ),
        checks=("check_ci_enforcement",),
    ),
]


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def harness_rule_text() -> str:
    files = [
        "AGENTS.md",
        "GEMINI.md",
        "PHYSICS.md",
        "README.md",
        "docs/hooks_reference.md",
        "docs/orchestration_protocol.md",
    ]
    return "\n".join(read_text(path) for path in files)


def run_manifest_check() -> list[str]:
    module_path = ROOT / "scripts" / "check_harness_manifest.py"
    spec = importlib.util.spec_from_file_location("check_harness_manifest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return list(module.validate_project(ROOT))


def run_spawn_contracts_check() -> list[str]:
    module_path = ROOT / "scripts" / "check_spawn_contracts.py"
    spec = importlib.util.spec_from_file_location("check_spawn_contracts", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return list(module.validate_project(ROOT))


def run_claim_promotion_lifecycle_check() -> list[str]:
    module_path = ROOT / "scripts" / "check_claim_promotion.py"
    spec = importlib.util.spec_from_file_location("check_claim_promotion", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_claim_promotion"] = module
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        (project / "docs" / "gates").mkdir(parents=True)
        (project / "docs" / "claims").mkdir(parents=True)
        (project / "outputs" / "data").mkdir(parents=True)
        (project / ".research-harness").write_text("evaluator fixture\n", encoding="utf-8")
        (project / "outputs" / "data" / "direct_read.csv").write_text(
            "evidence\n",
            encoding="utf-8",
        )
        (project / "docs" / "gates" / "validation_log.md").write_text(
            "# Validation Log\n\n"
            "| Date | Check | Target | Status | Evidence |\n"
            "|---|---|---|---|---|\n"
            "| 2026-05-26 | toy_model | claim_alpha | pass | outputs/data/direct_read.csv |\n"
            "| 2026-05-26 | conservation | claim_alpha | pass | outputs/data/direct_read.csv |\n",
            encoding="utf-8",
        )
        (project / "docs" / "claims" / "claim_alpha.md").write_text(
            "ceiling: mechanism\n\n"
            "## Claim\n\n"
            "outputs/data/direct_read.csv supports the mechanism.\n\n"
            "## Finding Lifecycle\n\n"
            "### Finding\n\n"
            "Status: independently_checked\n\n"
            "### Independent Check\n\n"
            "Result: independently_checked\n\n"
            "### Evidence Link\n\n"
            "Status: evidence_linked\n\n"
            "### Evidence Paths Read Directly\n\n"
            "- outputs/data/direct_read.csv\n",
            encoding="utf-8",
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = module.main(["--project", str(project), "--target", "mechanism"])
    return [] if code == 0 else [f"fixture mechanism promotion exited {code}"]


def run_ci_enforcement_check() -> list[str]:
    workflow = ROOT / ".github" / "workflows" / "harness-checks.yml"
    if not workflow.is_file():
        return ["missing .github/workflows/harness-checks.yml"]

    text = workflow.read_text(encoding="utf-8", errors="ignore")
    required_terms = [
        "push:",
        "pull_request:",
        "ubuntu-latest",
        "windows-latest",
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "python -m pip install -r requirements.txt",
        "python -m pytest tests -q",
        "python scripts/check_harness_manifest.py",
        "python scripts/check_spawn_contracts.py",
        "python scripts/check_contract_sync.py",
        "python scripts/evaluate_harness.py --fail-on-partial",
    ]
    problems = [
        f"workflow missing {term!r}"
        for term in required_terms
        if term not in text
    ]
    forbidden_terms = [
        "check_claim_promotion.py --project",
        "check_claim_promotion_freshness.py --project",
    ]
    problems.extend(
        f"workflow must not include {term!r}"
        for term in forbidden_terms
        if term in text
    )
    return problems


def run_scenario_checks(scenario: Scenario) -> list[str]:
    failures: list[str] = []
    for check in scenario.checks:
        if check == "check_harness_manifest":
            problems = run_manifest_check()
        elif check == "check_spawn_contracts":
            problems = run_spawn_contracts_check()
        elif check == "check_claim_promotion_lifecycle":
            problems = run_claim_promotion_lifecycle_check()
        elif check == "check_ci_enforcement":
            problems = run_ci_enforcement_check()
        else:
            problems = [f"unknown scenario check {check!r}"]
        if problems:
            failures.append(f"{check}: {'; '.join(problems)}")
    return failures


def evaluate_scenario(scenario: Scenario, rule_text: str) -> dict[str, object]:
    missing_skills = [path for path in scenario.skills if not (ROOT / path).exists()]
    missing_docs = [path for path in scenario.docs if not (ROOT / path).exists()]
    missing_terms = [
        term for term in scenario.rule_terms if term.lower() not in rule_text.lower()
    ]
    missing_checks = run_scenario_checks(scenario)

    total = (
        len(scenario.skills)
        + len(scenario.docs)
        + len(scenario.rule_terms)
        + len(scenario.checks)
    )
    missing = (
        len(missing_skills)
        + len(missing_docs)
        + len(missing_terms)
        + len(missing_checks)
    )
    score = 100 if total == 0 else round(100 * (total - missing) / total)

    if missing_checks:
        status = "fail"
    elif missing == 0:
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
        "missing_checks": missing_checks,
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
            ("missing_checks", "checks"),
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
