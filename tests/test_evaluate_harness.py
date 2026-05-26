import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_harness.py"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("evaluate_harness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["evaluate_harness"] = module
    spec.loader.exec_module(module)
    return module


def test_multi_agent_orchestration_scenarios_are_evaluated():
    evaluator = load_evaluator()

    names = [scenario.name for scenario in evaluator.SCENARIOS]

    assert "live_workflow_diagram_agent" in names
    assert "professor_orchestration" in names
    assert "graduate_test_design_agents" in names
    assert "coding_subagent_claim_discipline" in names
    assert "completion_conference_reporting" in names


def test_harness_evaluator_includes_hook_scenarios():
    evaluator = load_evaluator()

    assert len(evaluator.SCENARIOS) == 27


def test_orchestration_scenarios_require_run_templates():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert (
        "docs/run_templates/live_workflow_diagram_template.md"
        in scenarios["live_workflow_diagram_agent"].docs
    )
    assert (
        "docs/run_templates/research_run_packet_template.md"
        in scenarios["completion_conference_reporting"].docs
    )
    assert (
        "scripts/init_research_project.py"
        in scenarios["live_workflow_diagram_agent"].rule_terms
    )


def test_scientific_loop_hook_scenarios_are_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "hook_aware_scientific_loop" in scenarios
    assert "provenance_and_reproducibility_hooks" in scenarios
    assert "manuscript_and_artifact_drift_hooks" in scenarios
    assert "Task Intake Hook" in scenarios["hook_aware_scientific_loop"].rule_terms
    assert "Baseline Gate Hook" in scenarios["hook_aware_scientific_loop"].rule_terms
    assert (
        "Figure Provenance Hook"
        in scenarios["provenance_and_reproducibility_hooks"].rule_terms
    )
    assert (
        "Artifact Freshness Hook"
        in scenarios["manuscript_and_artifact_drift_hooks"].rule_terms
    )


def test_live_linked_research_graph_scenario_is_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "live_linked_research_graph" in scenarios


def test_user_facing_documentation_scenario_is_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "user_facing_documentation_drift" in scenarios
    assert "README.md" in scenarios["user_facing_documentation_drift"].docs
    assert "README.ko.md" in scenarios["user_facing_documentation_drift"].docs
    scenario = scenarios["live_linked_research_graph"]
    assert "docs/run_templates/live_workflow_diagram_template.md" in scenario.docs
    assert "docs/run_templates/research_run_packet_template.md" in scenario.docs
    assert "Link Status" in scenario.rule_terms
    assert "Evidence Strength" in scenario.rule_terms
    assert "Artifact Preview" in scenario.rule_terms
    assert "Staleness propagation" in scenario.rule_terms


def test_new_skill_scenarios_are_evaluated():
    evaluator = load_evaluator()

    names = [scenario.name for scenario in evaluator.SCENARIOS]

    assert "task_intake_orient_phase" in names
    assert "interview_gate_enforcement" in names
    assert "seed_design_graduate_tasks" in names
    assert "sync_workflow_lineage_frontmatter" in names


def test_interview_gate_enforcement_scenario_is_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}
    scenario = scenarios["interview_gate_enforcement"]

    assert "skills/professor-interview/SKILL.md" in scenario.skills
    assert "docs/run_templates/interview_notes_template.md" in scenario.docs
    assert "docs/run_templates/live_workflow_diagram_template.md" in scenario.docs
    assert "Interview Gate Hook" in scenario.rule_terms
    assert "check_interview_recorded.py" in scenario.rule_terms
    assert "before Seed or Execute work begins" in scenario.rule_terms


def test_literature_replanning_loop_scenario_is_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "literature_replanning_loop" in scenarios
    scenario = scenarios["literature_replanning_loop"]
    assert "skills/literature-review-planning/SKILL.md" in scenario.skills
    assert "docs/literature/README.md" in scenario.docs
    assert "docs/literature/paper_request_queue.md" in scenario.docs
    assert "docs/literature/paper_review_index_template.md" in scenario.docs
    assert "docs/literature/literature_review_template.md" in scenario.docs
    assert "docs/literature/replanning_memo_template.md" in scenario.docs
    assert "scripts/scaffold_paper_review.py" in scenario.docs
    assert "scripts/extract_paper_text.py" in scenario.docs
    assert "scripts/draft_paper_review.py" in scenario.docs
    assert "scripts/process_paper_for_review.py" in scenario.docs
    assert "scripts/check_paper_review_quality.py" in scenario.docs
    assert "Literature Replanning Hook" in scenario.rule_terms
    assert "researcher-provided PDFs" in scenario.rule_terms
    assert "novelty map" in scenario.rule_terms
    assert "section-by-section paper review" in scenario.rule_terms
    assert "Figure/Table-by-Figure/Table Review" in scenario.rule_terms
    assert "PDF text extraction is a reading aid" in scenario.rule_terms
    assert "Machine-Assisted Draft From Extracted Text" in scenario.rule_terms
    assert "process_paper_for_review.py" in scenario.rule_terms
    assert "clickable links across the literature graph" in scenario.rule_terms
    assert "check_paper_review_quality.py" in scenario.rule_terms


def test_computation_checkpoint_scenario_is_evaluated():
    evaluator = load_evaluator()

    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "computation_checkpoint_resumption" in scenarios
    scenario = scenarios["computation_checkpoint_resumption"]
    assert "skills/implementation-agent/SKILL.md" in scenario.skills
    assert "scripts/run_with_checkpoint.py" in scenario.docs
    assert "scripts/check_computation_resumable.py" in scenario.docs
    assert "Computation Checkpoint Hook" in scenario.rule_terms
    assert "CheckpointManager" in scenario.rule_terms
    assert "check_computation_resumable.py" in scenario.rule_terms
    assert "run_with_checkpoint.py" in scenario.rule_terms
    assert "cache/checkpoint_" in scenario.rule_terms
    assert "orphaned" in scenario.rule_terms


def test_capability_manifest_scenario_is_evaluated():
    evaluator = load_evaluator()
    scenarios = {scenario.name: scenario for scenario in evaluator.SCENARIOS}

    assert "capability_manifest_and_hook_registry" in scenarios
    scenario = scenarios["capability_manifest_and_hook_registry"]
    assert "docs/harness/capability_manifest.json" in scenario.docs
    assert "scripts/check_harness_manifest.py" in scenario.docs
    assert "Capability Manifest Hook" in scenario.rule_terms
    assert "hook registry" in scenario.rule_terms
    assert "workflow_gate_keys" in scenario.rule_terms
