#!/usr/bin/env python3
"""Create an optional typed domain workspace inside an existing project."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _layout as layout  # noqa: E402
import _project_root as project_root_mod  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "docs" / "run_templates" / "domain_manual_template.md"
DOMAIN_TYPES = ("reproduction", "thread", "subproblem", "integration")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _render_manual(domain_type: str) -> str:
    if TEMPLATE.exists():
        template = TEMPLATE.read_text(encoding="utf-8")
    else:
        template = "type: {{type}}\n"
    return template.replace("{{type}}", domain_type)


def _validate_name(name: str) -> str:
    if not SLUG_RE.fullmatch(name):
        raise ValueError(
            "Domain name must be a slug: lowercase letters, digits, hyphen, "
            "or underscore, starting with a letter or digit."
        )
    return name


def scaffold_domain(project: Path, name: str, domain_type: str) -> Path:
    """Create a domain workspace without changing project-level enforcement."""
    if domain_type not in DOMAIN_TYPES:
        allowed = ", ".join(DOMAIN_TYPES)
        raise ValueError(f"Invalid domain type '{domain_type}'. Expected one of: {allowed}.")

    name = _validate_name(name)
    if not (project / project_root_mod.MARKER_NAME).exists():
        raise project_root_mod.ProjectRootNotFoundError(
            f"No `{project_root_mod.MARKER_NAME}` marker found at {project}. "
            "Run init_research_project.py before adding domains."
        )

    domain_root = layout.domains_root(project) / name
    for directory in [
        layout.domain_src_dir(domain_root),
        layout.domain_figures_dir(domain_root),
        layout.domain_data_dir(domain_root),
        layout.domain_tables_dir(domain_root),
        layout.domain_plan_dir(domain_root),
        layout.domain_claims_dir(domain_root),
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    manual = layout.domain_manual(domain_root)
    if not manual.exists():
        manual.write_text(_render_manual(domain_type), encoding="utf-8")

    return domain_root


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project root or child path. Default: walk up from cwd looking "
             "for the `.research-harness` marker.",
    )
    parser.add_argument("--name", required=True, help="Domain slug to create.")
    parser.add_argument(
        "--type",
        required=True,
        dest="domain_type",
        help="Domain type: reproduction, thread, subproblem, or integration.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project = project_root_mod.find_project_root(args.project, require=True)
        domain_root = scaffold_domain(project, args.name, args.domain_type)
    except (ValueError, project_root_mod.ProjectRootNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Scaffolded domain workspace at {domain_root}")
    print(f"  Manual: {layout.domain_manual(domain_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
