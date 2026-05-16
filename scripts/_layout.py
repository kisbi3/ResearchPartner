"""Single source of truth for the research-run directory layout.

All gate check scripts, start_research_run.py, and run_with_capture.py
import from this module.  If the layout ever changes again, only this
file (and start_research_run.py) needs to be updated.

Run layout version: 2

Directory tree produced by start_research_run.py:

    <run>/
    ├── README.md
    ├── research_run_packet.md
    ├── docs/
    │   ├── gates/          ← gate artifacts (auto-checked by scripts)
    │   ├── plan/           ← planning & spec documents
    │   ├── process/        ← workflow tracking, reviews, retrospective
    │   ├── literature/     ← literature-review metadata
    │   └── meetings/       ← meeting notes
    ├── literature/         ← PDF files, reviews, extracted text
    ├── src/                ← all executable code
    ├── outputs/            ← final results (figures, data, tables)
    │   ├── figures/
    │   ├── data/
    │   └── tables/
    ├── cache/              ← recomputable intermediates (not committed)
    ├── logs/               ← stdout captures from src/ executions
    └── errors/             ← stderr / tracebacks from failed runs
"""

from __future__ import annotations

from pathlib import Path

LAYOUT_VERSION = "2"


# ── Sub-directory accessors ───────────────────────────────────────────────────

def gates_dir(run: Path) -> Path:
    """Gate artifacts checked automatically by gate scripts."""
    return run / "docs" / "gates"


def plan_dir(run: Path) -> Path:
    """Planning and specification documents."""
    return run / "docs" / "plan"


def process_dir(run: Path) -> Path:
    """Workflow tracking: live diagram, researcher reviews, retrospective."""
    return run / "docs" / "process"


def literature_dir(run: Path) -> Path:
    """Literature-review metadata (PDFs live in /literature/pdfs/)."""
    return run / "docs" / "literature"


# ── Gate artifacts  (docs/gates/) ────────────────────────────────────────────

def orient_note(run: Path) -> Path:
    return gates_dir(run) / "orient_note.md"


def interview_notes(run: Path) -> Path:
    return gates_dir(run) / "interview_notes.md"


def seed_design(run: Path) -> Path:
    return gates_dir(run) / "seed_design.md"


def baseline_registry(run: Path) -> Path:
    return gates_dir(run) / "baseline_registry.md"


def validation_log(run: Path) -> Path:
    return gates_dir(run) / "validation_log.md"


# ── Plan artifacts  (docs/plan/) ─────────────────────────────────────────────

def research_plan(run: Path) -> Path:
    return plan_dir(run) / "research_plan.md"


def model_spec(run: Path) -> Path:
    return plan_dir(run) / "model_spec.md"


def model_skip_waiver(run: Path) -> Path:
    return plan_dir(run) / "model_skip_waiver.md"


def baseline_strategy(run: Path) -> Path:
    return plan_dir(run) / "baseline_strategy.md"


# ── Process artifacts  (docs/process/) ───────────────────────────────────────

def live_workflow_diagram(run: Path) -> Path:
    return process_dir(run) / "live_workflow_diagram.md"


def cartographer_update_template(run: Path) -> Path:
    return process_dir(run) / "cartographer_update_template.md"


def researcher_review_log(run: Path) -> Path:
    return process_dir(run) / "researcher_review_log.md"


def research_retrospective(run: Path) -> Path:
    return process_dir(run) / "research_retrospective.md"


# ── Literature metadata  (docs/literature/) ──────────────────────────────────

def literature_review_plan(run: Path) -> Path:
    return literature_dir(run) / "literature_review_plan.md"


def literature_skip_waiver(run: Path) -> Path:
    return literature_dir(run) / "literature_skip_waiver.md"


def paper_request_queue(run: Path) -> Path:
    return literature_dir(run) / "paper_request_queue.md"


def replanning_memo(run: Path) -> Path:
    return literature_dir(run) / "replanning_memo.md"


# ── Runtime directories ───────────────────────────────────────────────────────

def src_dir(run: Path) -> Path:
    return run / "src"


def outputs_dir(run: Path) -> Path:
    return run / "outputs"


def cache_dir(run: Path) -> Path:
    return run / "cache"


def logs_dir(run: Path) -> Path:
    return run / "logs"


def errors_dir(run: Path) -> Path:
    return run / "errors"
