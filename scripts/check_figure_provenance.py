#!/usr/bin/env python3
"""Enforce figure provenance: every figure file must trace to a provenance record.

A figure file is any .png, .pdf, .svg, .jpg, or .jpeg under the scan root.
A figure passes if one of these is true:

1. A sibling provenance note exists at <figure-stem>.provenance.md.
2. A figure_provenance.md file in the same directory or any ancestor up to the
   scan root mentions the figure file's name.

Run with `--root <dir>`. Defaults to the current working directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


FIGURE_EXTS = {".png", ".pdf", ".svg", ".jpg", ".jpeg"}
PROVENANCE_INDEX = "figure_provenance.md"


def find_figures(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in FIGURE_EXTS
    )


def has_provenance(figure: Path, root: Path) -> bool:
    sibling = figure.with_suffix(".provenance.md")
    if sibling.exists():
        return True

    current = figure.parent
    root_resolved = root.resolve()
    while True:
        index = current / PROVENANCE_INDEX
        if index.exists():
            try:
                text = index.read_text(encoding="utf-8")
            except OSError:
                text = ""
            if figure.name in text:
                return True
        if current.resolve() == root_resolved:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return False


def check(root: Path) -> list[str]:
    if not root.exists():
        return [f"Scan root does not exist: {root}"]
    missing: list[str] = []
    for figure in find_figures(root):
        if not has_provenance(figure, root):
            try:
                rel = figure.relative_to(root)
            except ValueError:
                rel = figure
            missing.append(str(rel))
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that every figure has a traceable provenance record."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Directory to scan recursively (default: current directory).",
    )
    args = parser.parse_args(argv if argv is not None else [])
    root = Path(args.root).resolve()
    missing = check(root)

    if missing:
        print(f"Figure provenance check failed under {root}:")
        for entry in missing:
            print(f"  - {entry}")
        print(
            "Each figure needs either <stem>.provenance.md or a figure_provenance.md "
            "in an ancestor directory that names the figure file."
        )
        return 1

    print(f"Figure provenance check passed under {root}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
