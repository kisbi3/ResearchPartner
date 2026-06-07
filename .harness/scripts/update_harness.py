#!/usr/bin/env python3
"""Selectively update vendored Research Partner harness files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))

import _project_root as project_root_mod  # noqa: E402
from check_harness_version import read_lockfile  # noqa: E402
from install import (  # noqa: E402
    LOCKFILE_NAME,
    REPO_ZIP_URL,
    _owned_source_files,
    _sha256,
    _source_commit,
    _source_version,
    download_archive,
    local_source_root,
)


STATUS_ORDER = [
    "UPDATE",
    "ADD",
    "CONFLICT",
    "LOCAL-EDIT-KEPT",
    "REMOVED",
    "MISSING-LOCAL",
]


class SourceState:
    def __init__(self, root: Path, temp_dir: tempfile.TemporaryDirectory[str] | None = None) -> None:
        self.root = root
        self.temp_dir = temp_dir


class Plan:
    def __init__(
        self,
        *,
        source_files: dict[str, Path] | None = None,
        source_hashes: dict[str, str] | None = None,
        lock_files: dict[str, str] | None = None,
        next_lock_files: dict[str, str] | None = None,
    ) -> None:
        self.by_status = {status: [] for status in STATUS_ORDER}
        self.source_files = source_files or {}
        self.source_hashes = source_hashes or {}
        self.lock_files = lock_files or {}
        self.next_lock_files = next_lock_files or {}

    def add(self, status: str, rel_path: str) -> None:
        self.by_status.setdefault(status, []).append(rel_path)

    def status_paths(self, status: str) -> list[str]:
        return sorted(self.by_status.get(status, []))

    def changes_lock(self) -> bool:
        return self.next_lock_files != self.lock_files


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _resolve_source(args: argparse.Namespace) -> SourceState:
    if args.source:
        return SourceState(root=args.source.resolve())
    source_root = local_source_root()
    if source_root is not None:
        return SourceState(root=source_root.resolve())

    temp_dir = tempfile.TemporaryDirectory(prefix="researchpartner-update-")
    source_root = download_archive(args.archive_url, Path(temp_dir.name))
    return SourceState(root=source_root.resolve(), temp_dir=temp_dir)


def _source_file_map(source_root: Path) -> dict[str, Path]:
    source_files = _owned_source_files(source_root)
    if not source_files:
        raise FileNotFoundError("source has no harness-owned files to update")
    return {
        path.relative_to(source_root).as_posix(): path
        for path in source_files
    }


def _project_hash(project: Path, rel_path: str) -> str | None:
    path = project / rel_path
    if not path.is_file():
        return None
    return _sha256(path)


def _sidecar_path(project_path: Path) -> Path:
    return project_path.with_name(project_path.name + ".harness-new")


def _plan_update(project: Path, source_files: dict[str, Path], lock_files: dict[str, str]) -> Plan:
    source_hashes = {
        rel_path: _sha256(path)
        for rel_path, path in source_files.items()
    }
    plan = Plan(
        source_files=source_files,
        source_hashes=source_hashes,
        lock_files=dict(sorted(lock_files.items())),
        next_lock_files=dict(sorted(lock_files.items())),
    )

    for rel_path in sorted(set(source_files) | set(lock_files)):
        source_path = source_files.get(rel_path)
        locked_hash = lock_files.get(rel_path)
        project_hash = _project_hash(project, rel_path)

        if source_path is None:
            plan.add("REMOVED", rel_path)
            plan.next_lock_files.pop(rel_path, None)
            continue

        source_hash = source_hashes[rel_path]
        if locked_hash is None:
            if project_hash is not None and project_hash != source_hash:
                plan.add("CONFLICT", rel_path)
            else:
                plan.add("ADD", rel_path)
            plan.next_lock_files[rel_path] = source_hash
            continue

        if project_hash is None:
            plan.add("MISSING-LOCAL", rel_path)
            continue

        if project_hash == locked_hash:
            if source_hash != locked_hash:
                plan.add("UPDATE", rel_path)
                plan.next_lock_files[rel_path] = source_hash
            continue

        if source_hash != locked_hash:
            plan.add("CONFLICT", rel_path)
            plan.next_lock_files[rel_path] = source_hash
        else:
            plan.add("LOCAL-EDIT-KEPT", rel_path)

    plan.next_lock_files = dict(sorted(plan.next_lock_files.items()))
    return plan


def _write_lockfile(source_root: Path, project: Path, files: dict[str, str], installed_at: str | None) -> None:
    now = _now_utc()
    lock = {
        "lock_schema": 1,
        "harness_version": _source_version(source_root),
        "installed_at": installed_at or now,
        "updated_at": now,
        "files": dict(sorted(files.items())),
    }
    commit = _source_commit(source_root)
    if commit:
        lock["harness_commit"] = commit
    (project / LOCKFILE_NAME).write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _apply_plan(project: Path, source_root: Path, plan: Plan, installed_at: str | None) -> None:
    for status in ["UPDATE", "ADD"]:
        for rel_path in plan.status_paths(status):
            source = plan.source_files[rel_path]
            target = project / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    for rel_path in plan.status_paths("CONFLICT"):
        source = plan.source_files[rel_path]
        target = project / rel_path
        sidecar = _sidecar_path(target)
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, sidecar)

    if plan.changes_lock():
        _write_lockfile(source_root, project, plan.next_lock_files, installed_at)


def _adopt_project(project: Path, source_root: Path, source_files: dict[str, Path]) -> None:
    files: dict[str, str] = {}
    for rel_path in sorted(source_files):
        project_file = project / rel_path
        if project_file.is_file():
            files[rel_path] = _sha256(project_file)
    _write_lockfile(source_root, project, files, installed_at=None)


def _load_init_module(project: Path):
    module_path = project / ".harness" / "scripts" / "init_research_project.py"
    if not module_path.is_file():
        raise FileNotFoundError(
            ".harness/scripts/init_research_project.py missing; apply harness updates before refreshing hooks"
        )
    spec = importlib.util.spec_from_file_location("project_init_research_project", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _upgrade_hooks(project: Path) -> list[str]:
    init_module = _load_init_module(project)
    settings_path = project / ".claude" / "settings.local.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    harness_settings = json.loads(init_module._CLAUDE_SETTINGS_CONTENT)
    if not settings_path.exists():
        settings_path.write_text(init_module._CLAUDE_SETTINGS_CONTENT, encoding="utf-8")
        return ["created .claude/settings.local.json"]

    try:
        existing_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(existing_settings, dict):
            raise ValueError("top-level JSON is not an object")
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise ValueError(f"{settings_path} could not be parsed; hook refresh skipped ({exc})")

    merged, added = init_module._merge_hook_settings(existing_settings, harness_settings)
    if added:
        settings_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return added


def _print_plan(project: Path, source_root: Path, plan: Plan, *, apply: bool, upgrade_hooks: bool) -> None:
    mode = "apply" if apply else "dry-run"
    print(f"Harness update plan ({mode})")
    print(f"Project: {project}")
    print(f"Source: {source_root}")
    for status in STATUS_ORDER:
        paths = plan.status_paths(status)
        print(f"{status}: {len(paths)}")
        for rel_path in paths:
            print(f"- {rel_path}")
    if not apply:
        print("Dry run only; rerun with --apply to write harness updates.")
        if upgrade_hooks:
            print("Dry run only; hook refresh not applied.")
    elif upgrade_hooks:
        print("Hook refresh requested; applying after harness updates.")
    else:
        print(
            "Next: refresh hooks with "
            "`python .harness/scripts/init_research_project.py` from the project root."
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project root or child path. Default: walk up from cwd looking for .research-harness; if absent, use cwd.",
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write planned updates and refresh the lockfile.")
    mode.add_argument("--adopt", action="store_true", help="Stamp an unstamped legacy project without updating files.")
    mode.add_argument("--dry-run", action="store_true", help="Print the update plan without writing files.")
    parser.add_argument(
        "--upgrade-hooks",
        action="store_true",
        help="With --apply, merge current harness hook registration into .claude/settings.local.json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_state: SourceState | None = None
    try:
        project = project_root_mod.resolve_project(args.project, require=False)
        source_state = _resolve_source(args)
        source_root = source_state.root

        if source_root == project.resolve():
            raise ValueError("source and project must be different")

        source_files = _source_file_map(source_root)
        lock_path = project / LOCKFILE_NAME

        if args.adopt:
            if lock_path.is_file():
                raise ValueError(f"{LOCKFILE_NAME} already exists; run without --adopt")
            _adopt_project(project, source_root, source_files)
            print(f"Adopted current project owned files into {lock_path}")
            return 0

        if not lock_path.is_file():
            raise FileNotFoundError(f"{LOCKFILE_NAME} missing; run --adopt or reinstall")

        lock = read_lockfile(project)
        lock_files = lock["files"]
        plan = _plan_update(project, source_files, lock_files)
        apply = bool(args.apply)
        _print_plan(project, source_root, plan, apply=apply, upgrade_hooks=args.upgrade_hooks)
        if apply:
            _apply_plan(project, source_root, plan, lock.get("installed_at"))
            if args.upgrade_hooks:
                added_hooks = _upgrade_hooks(project)
                if added_hooks:
                    print(f"Hook refresh: merged {len(added_hooks)} harness enforcement hook(s).")
                else:
                    print("Hook refresh: hooks already current.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    finally:
        if source_state is not None and source_state.temp_dir is not None:
            source_state.temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
