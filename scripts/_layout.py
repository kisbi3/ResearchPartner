"""Single source of truth for the research-project directory layout.

After v3 the project root IS the research root — there is no
`ResearchPartner-runs/<date>-<slug>/` wrapping directory. All gate
artefacts, planning documents, process notes, literature reviews, source
code, and outputs live directly under the project root marked by
`.research-harness`.

Layout version: 3

Directory tree produced by `init_research_project.py`::

    <project>/
    ├── .research-harness        ← project-root marker (read by all scripts)
    ├── README.md
    ├── docs/
    │   ├── gates/               ← gate artefacts (auto-checked by scripts)
    │   ├── plan/                ← planning & spec documents
    │   ├── process/             ← workflow tracking, reviews, retrospective
    │   ├── literature/          ← literature-review metadata
    │   ├── meetings/            ← meeting notes
    │   ├── checkpoints/         ← stage checkpoints
    │   ├── claims/              ← per-claim notes (lineage-bearing)
    │   └── model_versions/      ← per-model-version notes (lineage-bearing)
    ├── literature/              ← PDF files, reviews, extracted text
    ├── src/                     ← all executable code
    ├── outputs/                 ← final results (figures, data, tables)
    │   ├── figures/
    │   ├── data/
    │   └── tables/
    ├── cache/                   ← recomputable intermediates (not committed)
    ├── logs/                    ← stdout captures from src/ executions
    └── errors/                  ← stderr / tracebacks from failed runs

All accessor functions take the project root as their argument. The old
`run`-named parameter is kept as an alias for one release so existing
callers do not break before migration; new code should use `project`.
"""

from __future__ import annotations

from pathlib import Path

LAYOUT_VERSION = "3"


# ── Sub-directory accessors ───────────────────────────────────────────────────

def gates_dir(project: Path) -> Path:
    """Gate artifacts checked automatically by gate scripts."""
    return project / "docs" / "gates"


def plan_dir(project: Path) -> Path:
    """Planning and specification documents."""
    return project / "docs" / "plan"


def process_dir(project: Path) -> Path:
    """Workflow tracking: live diagram, researcher reviews, retrospective."""
    return project / "docs" / "process"


def literature_dir(project: Path) -> Path:
    """Literature-review metadata (PDFs live in /literature/pdfs/)."""
    return project / "docs" / "literature"


# ── Gate artifacts  (docs/gates/) ────────────────────────────────────────────

def orient_note(project: Path) -> Path:
    return gates_dir(project) / "orient_note.md"


def interview_notes(project: Path) -> Path:
    return gates_dir(project) / "interview_notes.md"


def seed_design(project: Path) -> Path:
    return gates_dir(project) / "seed_design.md"


def baseline_registry(project: Path) -> Path:
    return gates_dir(project) / "baseline_registry.md"


def validation_log(project: Path) -> Path:
    return gates_dir(project) / "validation_log.md"


def agent_spawn_log(project: Path) -> Path:
    return gates_dir(project) / "agent_spawn_log.md"


def professor_evaluation(project: Path) -> Path:
    return gates_dir(project) / "professor_evaluation.md"


# ── Process completion markers  (docs/process/) ───────────────────────────────

def execution_complete(project: Path) -> Path:
    return process_dir(project) / "execution_complete.md"


def visualization_complete(project: Path) -> Path:
    return process_dir(project) / "visualization_complete.md"


def user_report(project: Path) -> Path:
    return process_dir(project) / "user_report.md"


# ── Plan artifacts  (docs/plan/) ─────────────────────────────────────────────

def research_plan(project: Path) -> Path:
    return plan_dir(project) / "research_plan.md"


def research_question(project: Path) -> Path:
    """One-line declarative statement of what this project is about."""
    return plan_dir(project) / "research_question.md"


def model_spec(project: Path) -> Path:
    return plan_dir(project) / "model_spec.md"


def model_skip_waiver(project: Path) -> Path:
    return plan_dir(project) / "model_skip_waiver.md"


def baseline_strategy(project: Path) -> Path:
    return plan_dir(project) / "baseline_strategy.md"


# ── Process artifacts  (docs/process/) ───────────────────────────────────────

def live_workflow_diagram(project: Path) -> Path:
    return process_dir(project) / "live_workflow_diagram.md"


def cartographer_update_template(project: Path) -> Path:
    return process_dir(project) / "cartographer_update_template.md"


def researcher_review_log(project: Path) -> Path:
    return process_dir(project) / "researcher_review_log.md"


def research_retrospective(project: Path) -> Path:
    return process_dir(project) / "research_retrospective.md"


# ── Literature metadata  (docs/literature/) ──────────────────────────────────

def literature_review_plan(project: Path) -> Path:
    return literature_dir(project) / "literature_review_plan.md"


def literature_skip_waiver(project: Path) -> Path:
    return literature_dir(project) / "literature_skip_waiver.md"


def paper_request_queue(project: Path) -> Path:
    return literature_dir(project) / "paper_request_queue.md"


def replanning_memo(project: Path) -> Path:
    return literature_dir(project) / "replanning_memo.md"


# ── Lineage / claim / model-version dirs (signal artefacts) ──────────────────

def claims_dir(project: Path) -> Path:
    return project / "docs" / "claims"


def model_versions_dir(project: Path) -> Path:
    return project / "docs" / "model_versions"


def meetings_dir(project: Path) -> Path:
    return project / "docs" / "meetings"


def checkpoints_dir(project: Path) -> Path:
    return project / "docs" / "checkpoints"


# ── Runtime directories ───────────────────────────────────────────────────────

def src_dir(project: Path) -> Path:
    return project / "src"


def outputs_dir(project: Path) -> Path:
    return project / "outputs"


def cache_dir(project: Path) -> Path:
    return project / "cache"


def logs_dir(project: Path) -> Path:
    return project / "logs"


def errors_dir(project: Path) -> Path:
    return project / "errors"


def literature_pdf_dir(project: Path) -> Path:
    return project / "literature" / "pdfs"


def literature_reviews_dir(project: Path) -> Path:
    return project / "literature" / "reviews"


def literature_extracted_dir(project: Path) -> Path:
    return project / "literature" / "extracted_text"


# ── Workflow-map artefacts at project root ───────────────────────────────────

def workflow_map_html(project: Path) -> Path:
    return project / "workflow_map.html"


def workflow_map_live_json(project: Path) -> Path:
    return project / "workflow_map.live.json"
