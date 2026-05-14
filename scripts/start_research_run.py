#!/usr/bin/env python3
"""Create a research-run directory from the harness run templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_ROOT = ROOT.parent / "ResearchPartner-runs"
LIVE_TEMPLATE = ROOT / "docs" / "run_templates" / "live_workflow_diagram_template.md"
PACKET_TEMPLATE = ROOT / "docs" / "run_templates" / "research_run_packet_template.md"
CARTOGRAPHER_UPDATE_TEMPLATE = (
    ROOT / "docs" / "run_templates" / "cartographer_update_template.md"
)

INITIAL_DOCS = {
    "research_plan.md": "# Research Plan\n\n- Run-specific plan seed:\n",
    "baseline_registry.md": "# Baseline Registry\n\n- Run-specific baseline target:\n",
    "validation_log.md": "# Validation Log\n\n| Date | Command | Result | Evidence |\n|---|---|---|---|\n",
    "researcher_review_log.md": "# Researcher Review Log\n\n| Date | Evidence Shown | Decision | Follow-up |\n|---|---|---|---|\n",
    "research_retrospective.md": "# Research Retrospective\n\n- Reusable artifact:\n- Next smallest useful iteration:\n",
}


def slugify_name(name: str) -> str:
    """Return a lowercase hyphenated ASCII-ish slug for a run name."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError("Run name must contain at least one letter or number.")
    return slug


def create_run(name: str, date_text: str | None = None, runs_root: Path | str = DEFAULT_RUNS_ROOT) -> Path:
    """Create and return a new run directory."""
    run_date = date_text or date.today().isoformat()
    slug = slugify_name(name)
    runs_root = Path(runs_root)
    run_path = runs_root / f"{run_date}-{slug}"

    if run_path.exists():
        raise FileExistsError(f"Run already exists: {run_path}")

    docs_dir = run_path / "docs"
    outputs_dir = run_path / "outputs"
    docs_dir.mkdir(parents=True)
    outputs_dir.mkdir()

    shutil.copyfile(LIVE_TEMPLATE, docs_dir / "live_workflow_diagram.md")
    shutil.copyfile(PACKET_TEMPLATE, run_path / "research_run_packet.md")
    shutil.copyfile(
        CARTOGRAPHER_UPDATE_TEMPLATE,
        docs_dir / "cartographer_update_template.md",
    )

    for filename, content in INITIAL_DOCS.items():
        (docs_dir / filename).write_text(content, encoding="utf-8")

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
