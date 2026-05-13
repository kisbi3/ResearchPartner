#!/usr/bin/env python3
"""Create a lightweight intake report for an existing physics project."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys


COMMON_DIRS = [
    "src",
    "scripts",
    "notebooks",
    "data",
    "results",
    "figures",
    "plots",
    "manuscript",
    "paper",
    "docs",
]

INTERESTING_SUFFIXES = {
    ".py": "python",
    ".ipynb": "notebook",
    ".tex": "tex",
    ".md": "markdown",
    ".csv": "data",
    ".tsv": "data",
    ".json": "json",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".png": "figure",
    ".jpg": "figure",
    ".jpeg": "figure",
    ".pdf": "pdf",
    ".svg": "figure",
}

HARNESS_PATHS = [
    "AGENTS.md",
    "GEMINI.md",
    "PHYSICS.md",
    "skills/baseline-validation/SKILL.md",
    "docs/baseline_registry.md",
    "docs/existing_project_intake.md",
    "docs/retrofit_validation_plan.md",
]

BANNED_MATPLOTLIB_SHOW = "plt." + "show("


def count_interesting_files(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    ignored_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules"}
    for path in root.rglob("*"):
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.is_dir():
            continue
        label = INTERESTING_SUFFIXES.get(path.suffix.lower())
        if label:
            counts[label] += 1
    return counts


def find_directories(root: Path) -> list[str]:
    return [directory for directory in COMMON_DIRS if (root / directory).is_dir()]


def find_harness_paths(root: Path) -> list[str]:
    return [path for path in HARNESS_PATHS if (root / path).exists()]


def scan_for_matplotlib_show(root: Path) -> list[str]:
    matches = []
    for directory in ["src", "scripts", "notebooks"]:
        base = root / directory
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
                matches.append(str(path.relative_to(root)))
    return matches


def make_report(root: Path) -> str:
    directories = find_directories(root)
    counts = count_interesting_files(root)
    harness = find_harness_paths(root)
    show_matches = scan_for_matplotlib_show(root)
    has_git = (root / ".git").exists()

    lines = [
        "# Existing Project Audit",
        "",
        f"- Root: `{root}`",
        f"- Git metadata present: {'yes' if has_git else 'no'}",
        "",
        "## Common Directories",
        "",
    ]
    if directories:
        lines.extend(f"- `{directory}/`" for directory in directories)
    else:
        lines.append("- None detected")

    lines.extend(["", "## File Type Counts", ""])
    if counts:
        for label, count in sorted(counts.items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No common research file types detected")

    lines.extend(["", "## Harness Files Present", ""])
    if harness:
        lines.extend(f"- `{path}`" for path in harness)
    else:
        lines.append("- No harness files detected")

    lines.extend(["", "## Potential Issues", ""])
    if show_matches:
        lines.append(f"- Found direct `{BANNED_MATPLOTLIB_SHOW})` usage in:")
        lines.extend(f"  - `{path}`" for path in show_matches)
    else:
        lines.append("- No direct matplotlib show calls detected in common code directories")

    lines.extend(
        [
            "",
            "## Suggested First Retrofit Target",
            "",
            "Choose one narrow target: reproduce one existing figure, validate one toy model, audit one simulation pipeline, or map one manuscript section to evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit an existing physics project before attaching the research harness."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to audit. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a markdown report. Prints to stdout when omitted.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    report = make_report(root)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
