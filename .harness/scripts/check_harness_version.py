#!/usr/bin/env python3
"""Report installed Research Partner harness stamp and local owned-file drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402

LOCKFILE_NAME = "harness.lock.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_lockfile(project: Path) -> dict:
    lock_path = project / LOCKFILE_NAME
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {LOCKFILE_NAME}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {LOCKFILE_NAME}: {exc}") from exc

    if data.get("lock_schema") != 1:
        raise ValueError(f"invalid {LOCKFILE_NAME}: lock_schema must be 1")
    files = data.get("files")
    if not isinstance(files, dict) or not all(
        isinstance(path, str) and isinstance(digest, str)
        for path, digest in files.items()
    ):
        raise ValueError(f"invalid {LOCKFILE_NAME}: files must be an object of path -> sha256")
    return data


def local_modifications(project: Path, files: dict[str, str]) -> list[str]:
    modified: list[str] = []
    for rel_path, expected_hash in sorted(files.items()):
        path = project / rel_path
        if not path.is_file():
            modified.append(f"{rel_path} (missing)")
            continue
        if _sha256(path) != expected_hash:
            modified.append(rel_path)
    return modified


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project root or child path. Default: walk up from cwd looking for "
             ".research-harness; if absent, use cwd.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project = project_root_mod.resolve_project(args.project, require=False)
    lock_path = project / LOCKFILE_NAME
    if not lock_path.is_file():
        print("Harness stamp: not stamped; run install to stamp this project.")
        return 0

    try:
        lock = read_lockfile(project)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    files = lock["files"]
    modified = local_modifications(project, files)
    print(f"Harness version: {lock.get('harness_version') or '(unknown)'}")
    print(f"Harness commit: {lock.get('harness_commit') or '(unknown)'}")
    print(f"Installed at: {lock.get('installed_at') or '(unknown)'}")
    print(f"Updated at: {lock.get('updated_at') or '(unknown)'}")
    print(f"tracked owned files: {len(files)}")
    print(f"local modifications: {len(modified)}")
    for rel_path in modified:
        print(f"- {rel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
