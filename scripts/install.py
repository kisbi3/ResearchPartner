#!/usr/bin/env python3
"""Install Research Partner harness files into a research project root."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


REPO_ZIP_URL = "https://github.com/kisbi3/ResearchPartner/archive/refs/heads/main.zip"
MANAGED_ITEMS = ("AGENTS.md", "GEMINI.md", "PHYSICS.md", "skills", "docs", "scripts")


def display_name(item: str) -> str:
    return f"{item}/" if item in {"skills", "docs", "scripts"} else item


def install_from_source(source_root: Path, target_root: Path, force: bool = False) -> list[str]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    missing = [item for item in MANAGED_ITEMS if not (source_root / item).exists()]
    if missing:
        raise FileNotFoundError(f"source is missing required harness item(s): {', '.join(missing)}")

    existing = [item for item in MANAGED_ITEMS if (target_root / item).exists()]
    if existing and not force:
        names = ", ".join(display_name(item) for item in existing)
        raise FileExistsError(
            f"target already contains managed harness item(s): {names}; rerun with --force to overwrite"
        )

    installed: list[str] = []
    for item in MANAGED_ITEMS:
        source = source_root / item
        target = target_root / item
        if target.exists() and force:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        installed.append(display_name(item))

    return installed


def download_archive(url: str, work_dir: Path) -> Path:
    archive_path = work_dir / "researchpartner.zip"
    urllib.request.urlretrieve(url, archive_path)
    extract_dir = work_dir / "extract"
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_dir)

    roots = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"expected one extracted repository root, found {len(roots)}")
    return roots[0]


def local_source_root() -> Path | None:
    script_path = Path(__file__).resolve() if "__file__" in globals() else None
    if not script_path:
        return None
    candidate = script_path.parents[1]
    if all((candidate / item).exists() for item in MANAGED_ITEMS):
        return candidate
    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Project root to install into. Defaults to the current directory.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Local Research Partner source checkout. Defaults to this checkout or the GitHub main archive.",
    )
    parser.add_argument(
        "--archive-url",
        default=REPO_ZIP_URL,
        help="Repository ZIP URL used when no local source is available.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing harness-managed files and directories in the target.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        source_root = args.source.resolve() if args.source else local_source_root()
        if source_root:
            installed = install_from_source(source_root, args.target, force=args.force)
        else:
            with tempfile.TemporaryDirectory(prefix="researchpartner-install-") as tmp:
                source_root = download_archive(args.archive_url, Path(tmp))
                installed = install_from_source(source_root, args.target, force=args.force)
    except Exception as exc:
        print(f"Research Partner install failed: {exc}", file=sys.stderr)
        return 1

    print(f"Installed Research Partner into {args.target.resolve()}")
    for item in installed:
        print(f"- {item}")
    print("Next: launch your AI assistant in this project root and ask for a research-plan-review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
