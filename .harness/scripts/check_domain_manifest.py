#!/usr/bin/env python3
"""Validate optional domain workspace manuals.

This checker is intentionally dormant for legacy projects with no
``domains/`` directory. When a project opts into domains, it validates only
manual structure: README presence, a known ``type``, and required field keys.
It does not judge field contents or enforce per-domain scientific semantics.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _layout as layout  # noqa: E402
import _project_root as project_root_mod  # noqa: E402

DOMAIN_TYPES = {"reproduction", "thread", "subproblem", "integration"}
REQUIRED_TOP_LEVEL_FIELDS = [
    "type",
    "purpose",
    "ground-truth",
    "pass-fail",
    "units",
    "assumptions",
    "relations",
    "claim-ceiling-cap",
]
REQUIRED_RELATION_FIELDS = ["depends-on", "integrates-into"]
_FIELD_RE_TEMPLATE = r"^\s*{field}\s*[:=]"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _has_field(text: str, field: str) -> bool:
    return re.search(
        _FIELD_RE_TEMPLATE.format(field=re.escape(field)),
        text,
        flags=re.MULTILINE,
    ) is not None


def _type_value(text: str) -> str:
    match = re.search(r"^\s*type\s*[:=]\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def validate_project(project: Path | str) -> list[str]:
    project = Path(project).resolve()
    problems: list[str] = []

    for domain_root in layout.domains(project):
        if domain_root == project:
            continue

        domain_label = domain_root.relative_to(project).as_posix()
        manual = layout.domain_manual(domain_root)
        if not manual.is_file():
            problems.append(f"{domain_label}: missing README.md")
            continue

        text = _read(manual)
        domain_type = _type_value(text)
        if not domain_type:
            problems.append(f"{domain_label}: missing required field type")
        elif domain_type not in DOMAIN_TYPES:
            allowed = ", ".join(sorted(DOMAIN_TYPES))
            problems.append(
                f"{domain_label}: invalid type {domain_type!r}; expected one of: {allowed}"
            )

        for field in REQUIRED_TOP_LEVEL_FIELDS:
            if not _has_field(text, field):
                problems.append(f"{domain_label}: missing required field {field}")

        for field in REQUIRED_RELATION_FIELDS:
            if not _has_field(text, field):
                problems.append(f"{domain_label}: missing required field relations.{field}")

    return problems


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project root or child path. Default: walk up from cwd looking "
             "for `.research-harness`; if absent, use cwd. Projects with no "
             "`domains/` directory exit 0.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project = project_root_mod.resolve_project(args.project, require=False)
    problems = validate_project(project)
    if problems:
        print("Domain manifest check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    print("Domain manifest check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
