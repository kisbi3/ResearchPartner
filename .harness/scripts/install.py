#!/usr/bin/env python3
"""Install Research Partner harness files into a research project root."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


REPO_ZIP_URL = "https://github.com/kisbi3/ResearchPartner/archive/refs/heads/main.zip"
OWNED_PATHS_MANIFEST = Path("docs/harness/owned_paths.json")
LOCKFILE_NAME = "harness.lock.json"


def display_name(item: str) -> str:
    return item


def _read_owned_globs(source_root: Path) -> list[str]:
    manifest_path = source_root / OWNED_PATHS_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"source is missing required owned-path manifest: {OWNED_PATHS_MANIFEST}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("owned"), list):
        raise ValueError(f"invalid owned-path manifest: {OWNED_PATHS_MANIFEST}")
    globs: list[str] = []
    for item in data["owned"]:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"invalid owned path entry in {OWNED_PATHS_MANIFEST}: {item!r}")
        globs.append(item.strip().replace("\\", "/"))
    return globs


def _owned_source_files(source_root: Path) -> list[Path]:
    files: dict[str, Path] = {}
    for pattern in _read_owned_globs(source_root):
        if any(char in pattern for char in "*?["):
            matches = sorted(source_root.glob(pattern))
        else:
            matches = [source_root / pattern]
        for path in matches:
            if path.is_file():
                rel = path.relative_to(source_root).as_posix()
                files[rel] = path
    return [files[key] for key in sorted(files)]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_commit(source_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def _source_version(source_root: Path) -> str | None:
    version_path = source_root / "VERSION"
    if not version_path.is_file():
        return None
    value = version_path.read_text(encoding="utf-8", errors="ignore").strip()
    return value or None


def _existing_installed_at(lock_path: Path) -> str | None:
    if not lock_path.is_file():
        return None
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    value = data.get("installed_at")
    return value if isinstance(value, str) and value else None


def _write_lockfile(source_root: Path, target_root: Path, rel_paths: list[str]) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lock_path = target_root / LOCKFILE_NAME
    installed_at = _existing_installed_at(lock_path) or now
    files = {
        rel_path: _sha256(target_root / rel_path)
        for rel_path in sorted(rel_paths)
        if (target_root / rel_path).is_file()
    }
    lock = {
        "lock_schema": 1,
        "harness_version": _source_version(source_root),
        "installed_at": installed_at,
        "updated_at": now,
        "files": files,
    }
    commit = _source_commit(source_root)
    if commit:
        lock["harness_commit"] = commit
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_from_source(source_root: Path, target_root: Path, force: bool = False) -> list[str]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    source_files = _owned_source_files(source_root)
    if not source_files:
        raise FileNotFoundError("source has no harness-owned files to install")

    rel_paths = [path.relative_to(source_root).as_posix() for path in source_files]
    existing = [rel_path for rel_path in rel_paths if (target_root / rel_path).exists()]
    if existing and not force:
        names = ", ".join(display_name(item) for item in existing)
        raise FileExistsError(
            f"target already contains managed harness item(s): {names}; rerun with --force to overwrite"
        )

    installed: list[str] = []
    for source in source_files:
        rel_path = source.relative_to(source_root).as_posix()
        target = target_root / rel_path
        if target.exists() and target.is_dir():
            if not force:
                raise FileExistsError(
                    f"target path is a directory where a harness-owned file is expected: {rel_path}"
                )
            if target.is_dir():
                shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        installed.append(display_name(rel_path))

    _write_lockfile(source_root, target_root, rel_paths)

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
    candidate = script_path.parents[2]
    if (candidate / OWNED_PATHS_MANIFEST).is_file():
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
