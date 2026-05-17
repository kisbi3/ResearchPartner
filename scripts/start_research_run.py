#!/usr/bin/env python3
"""Create a research-run directory from the harness run templates.

Layout version: 2

Directory structure created:

    <run>/
    ├── README.md
    ├── research_run_packet.md
    ├── .gitignore
    ├── docs/
    │   ├── gates/          ← orient_note, interview_notes, seed_design,
    │   │                      baseline_registry, validation_log
    │   ├── plan/           ← research_plan, model_spec, baseline_strategy
    │   ├── process/        ← live_workflow_diagram, researcher_review_log,
    │   │                      research_retrospective, cartographer_update_template
    │   ├── literature/     ← literature_review_plan, paper_request_queue,
    │   │                      replanning_memo
    │   └── meetings/
    ├── literature/
    │   ├── pdfs/
    │   ├── reviews/
    │   ├── extracted_text/
    │   └── index.md
    ├── src/
    ├── outputs/
    │   ├── figures/
    │   ├── data/
    │   └── tables/
    ├── cache/
    ├── logs/
    └── errors/
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import shutil
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _layout as layout  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_ROOT = ROOT.parent / "ResearchPartner-runs"

# ── Template sources ──────────────────────────────────────────────────────────
LIVE_TEMPLATE = ROOT / "docs" / "run_templates" / "live_workflow_diagram_template.md"
PACKET_TEMPLATE = ROOT / "docs" / "run_templates" / "research_run_packet_template.md"
CARTOGRAPHER_UPDATE_TEMPLATE = (
    ROOT / "docs" / "run_templates" / "cartographer_update_template.md"
)
ORIENT_NOTE_TEMPLATE = ROOT / "docs" / "run_templates" / "orient_note_template.md"
INTERVIEW_NOTES_TEMPLATE = ROOT / "docs" / "run_templates" / "interview_notes_template.md"
MODEL_SPEC_TEMPLATE = ROOT / "docs" / "run_templates" / "model_spec_template.md"
BASELINE_STRATEGY_TEMPLATE = (
    ROOT / "docs" / "run_templates" / "baseline_strategy_template.md"
)
README_TEMPLATE = ROOT / "docs" / "run_templates" / "run_readme_template.md"
LITERATURE_REVIEW_TEMPLATE = ROOT / "docs" / "literature" / "literature_review_template.md"
PAPER_REQUEST_TEMPLATE = ROOT / "docs" / "literature" / "paper_request_queue.md"
REPLANNING_MEMO_TEMPLATE = ROOT / "docs" / "literature" / "replanning_memo_template.md"
PAPER_REVIEW_INDEX_TEMPLATE = (
    ROOT / "docs" / "literature" / "paper_review_index_template.md"
)

# ── Files created from inline content ────────────────────────────────────────
INITIAL_GATES = {
    "baseline_registry.md": "# Baseline Registry\n\n- Run-specific baseline target:\n",
    "validation_log.md": (
        "# Validation Log\n\n"
        "| Date | Command | Result | Evidence |\n"
        "|---|---|---|---|\n"
    ),
}

INITIAL_PLAN = {
    "research_plan.md": "# Research Plan\n\n- Run-specific plan seed:\n",
}

INITIAL_PROCESS = {
    "researcher_review_log.md": (
        "# Researcher Review Log\n\n"
        "| Date | Evidence Shown | Decision | Follow-up |\n"
        "|---|---|---|---|\n"
    ),
    "research_retrospective.md": (
        "# Research Retrospective\n\n"
        "- Reusable artifact:\n"
        "- Next smallest useful iteration:\n"
    ),
}

_GITIGNORE_CONTENT = """\
# Research run — auto-generated .gitignore
# These directories are excluded because they contain recomputable or
# session-local data.  All other directories ARE committed.

cache/
logs/
errors/
literature/pdfs/
"""


def slugify_name(name: str) -> str:
    """Return a lowercase hyphenated ASCII-ish slug for a run name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError("Run name must contain at least one letter or number.")
    return slug


def create_run(
    name: str,
    date_text: str | None = None,
    runs_root: Path | str = DEFAULT_RUNS_ROOT,
) -> Path:
    """Create and return a new run directory."""
    run_date = date_text or date.today().isoformat()
    slug = slugify_name(name)
    runs_root = Path(runs_root)
    run_path = runs_root / f"{run_date}-{slug}"

    if run_path.exists():
        raise FileExistsError(f"Run already exists: {run_path}")

    # ── Create directory tree ─────────────────────────────────────────────────
    for d in [
        layout.gates_dir(run_path),
        layout.plan_dir(run_path),
        layout.process_dir(run_path),
        layout.literature_dir(run_path),
        run_path / "docs" / "meetings",
        run_path / "literature" / "pdfs",
        run_path / "literature" / "reviews",
        run_path / "literature" / "extracted_text",
        layout.src_dir(run_path),
        layout.outputs_dir(run_path) / "figures",
        layout.outputs_dir(run_path) / "data",
        layout.outputs_dir(run_path) / "tables",
        layout.cache_dir(run_path),
        layout.logs_dir(run_path),
        layout.errors_dir(run_path),
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Copy template files → docs/gates/ ────────────────────────────────────
    gates = layout.gates_dir(run_path)
    shutil.copyfile(ORIENT_NOTE_TEMPLATE, gates / "orient_note.md")
    shutil.copyfile(INTERVIEW_NOTES_TEMPLATE, gates / "interview_notes.md")

    # ── Copy template files → docs/plan/ ─────────────────────────────────────
    plan = layout.plan_dir(run_path)
    shutil.copyfile(MODEL_SPEC_TEMPLATE, plan / "model_spec.md")
    shutil.copyfile(BASELINE_STRATEGY_TEMPLATE, plan / "baseline_strategy.md")

    # ── Copy template files → docs/process/ ──────────────────────────────────
    process = layout.process_dir(run_path)
    shutil.copyfile(LIVE_TEMPLATE, process / "live_workflow_diagram.md")
    shutil.copyfile(CARTOGRAPHER_UPDATE_TEMPLATE, process / "cartographer_update_template.md")

    # ── Copy template files → docs/literature/ ───────────────────────────────
    lit = layout.literature_dir(run_path)
    shutil.copyfile(LITERATURE_REVIEW_TEMPLATE, lit / "literature_review_plan.md")
    shutil.copyfile(PAPER_REQUEST_TEMPLATE, lit / "paper_request_queue.md")
    shutil.copyfile(REPLANNING_MEMO_TEMPLATE, lit / "replanning_memo.md")

    # ── Copy template files → run root ────────────────────────────────────────
    shutil.copyfile(PACKET_TEMPLATE, run_path / "research_run_packet.md")
    if README_TEMPLATE.exists():
        shutil.copyfile(README_TEMPLATE, run_path / "README.md")

    # ── Copy paper review index → literature/ ────────────────────────────────
    shutil.copyfile(PAPER_REVIEW_INDEX_TEMPLATE, run_path / "literature" / "index.md")

    # ── Write inline-content files ────────────────────────────────────────────
    for filename, content in INITIAL_GATES.items():
        (gates / filename).write_text(content, encoding="utf-8")

    for filename, content in INITIAL_PLAN.items():
        (plan / filename).write_text(content, encoding="utf-8")

    for filename, content in INITIAL_PROCESS.items():
        (process / filename).write_text(content, encoding="utf-8")

    # ── Write .gitignore ──────────────────────────────────────────────────────
    (run_path / ".gitignore").write_text(_GITIGNORE_CONTENT, encoding="utf-8")

    # ── Bootstrap live workflow JSON + HTML ───────────────────────────────────
    # This allows workflow_map.html to be opened immediately and updated by
    # agents via update_live_json.py without needing generate_workflow_map.py.
    try:
        import update_live_json as ulj  # noqa: PLC0415
        ulj.bootstrap_run_json(run_path)
    except Exception:
        pass  # Non-fatal: agents can call update_live_json.py manually.

    return run_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Human-readable research run name.")
    parser.add_argument(
        "--date",
        dest="date_text",
        help="Run date prefix in YYYY-MM-DD form. Defaults to today.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help="Directory that will contain run directories.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_path = create_run(
        name=args.name,
        date_text=args.date_text,
        runs_root=args.runs_root,
    )
    print(f"Created {run_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
