#!/usr/bin/env python3
"""Validate the harness capability manifest against runnable repo state."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path("docs/harness/capability_manifest.json")
MIN_CAPABILITIES = 8
PROJECT_DIR_TOKEN = "$CLAUDE_PROJECT_DIR/.harness/scripts/"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def _workflow_gate_keys(project: Path) -> set[str]:
    source = project / ".harness" / "scripts" / "generate_workflow_map.py"
    if not source.exists():
        return set()

    tree = ast.parse(source.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
            value = node.value
        else:
            continue
        if not {"_GATE_SPECIFIC_LINK_PATHS", "GATE_RESULT_BUILDERS"}.intersection(targets):
            continue
        if not isinstance(value, ast.Dict):
            continue
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)
    return keys


def _command_script(command: str) -> str:
    token_match = re.search(r"\$CLAUDE_PROJECT_DIR/.harness/scripts/([^\"\s]+)", command)
    if token_match:
        return f".harness/scripts/{token_match.group(1)}"
    relative_match = re.search(r"\b.harness/scripts/([^\"\s]+)", command)
    if relative_match:
        return f".harness/scripts/{relative_match.group(1)}"
    return ""


def _wired_hooks(settings_path: Path) -> list[dict[str, str]]:
    if not settings_path.exists():
        return []
    data = _load_json(settings_path)
    hooks = data.get("hooks", {})
    wired: list[dict[str, str]] = []
    if not isinstance(hooks, dict):
        return wired

    for event, blocks in hooks.items():
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            matcher = str(block.get("matcher", ""))
            for hook in block.get("hooks", []):
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command")
                if isinstance(command, str):
                    wired.append(
                        {
                            "event": str(event),
                            "matcher": matcher,
                            "command": command,
                            "script": _command_script(command),
                        }
                    )
    return wired


def _local_settings_problems(settings_path: Path) -> list[str]:
    if not settings_path.exists():
        return []
    data = _load_json(settings_path)
    if data.get("permissions"):
        return [
            ".claude/settings.local.json contains local permissions; "
            "tracked harness settings must only register portable hooks"
        ]
    return []


def validate_manifest(project: Path | str, manifest_path: Path | str) -> list[str]:
    project = Path(project)
    manifest_path = Path(manifest_path)
    problems: list[str] = []

    if not manifest_path.exists():
        return [f"missing manifest: {manifest_path}"]

    try:
        manifest = _load_json(manifest_path)
    except ValueError as exc:
        return [str(exc)]

    if manifest.get("schema_version") != 1:
        problems.append("schema_version must be 1")

    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list):
        problems.append("capabilities must be a list")
        capabilities = []
    elif len(capabilities) < MIN_CAPABILITIES:
        problems.append(
            f"capabilities must include at least {MIN_CAPABILITIES} entries; found {len(capabilities)}"
        )

    allowed_gate_keys = _workflow_gate_keys(project)
    capability_ids: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            problems.append(f"capabilities[{index}] must be an object")
            continue
        capability_id = str(capability.get("id", "")).strip()
        if not capability_id:
            problems.append(f"capabilities[{index}] missing id")
        elif capability_id in capability_ids:
            problems.append(f"duplicate capability id: {capability_id}")
        capability_ids.add(capability_id)

        for field in ("title", "kind", "enforcement"):
            if not str(capability.get(field, "")).strip():
                problems.append(f"{capability_id or index}: missing {field}")

        for script in _string_list(capability.get("scripts")):
            if not (project / script).exists():
                problems.append(f"{capability_id}: missing script {script}")
        for doc in _string_list(capability.get("docs")):
            if not (project / doc).exists():
                problems.append(f"{capability_id}: missing doc {doc}")
        for key in _string_list(capability.get("workflow_gate_keys")):
            if key not in allowed_gate_keys:
                problems.append(
                    f"{capability_id}: workflow_gate_keys contains unknown key {key!r}"
                )

    hook_registry = manifest.get("hook_registry")
    if not isinstance(hook_registry, list):
        problems.append("hook_registry must be a list")
        hook_registry = []

    registered_scripts: set[str] = set()
    for index, hook in enumerate(hook_registry):
        if not isinstance(hook, dict):
            problems.append(f"hook_registry[{index}] must be an object")
            continue
        hook_id = str(hook.get("id", f"hook_registry[{index}]"))
        command = str(hook.get("command", ""))
        script = str(hook.get("script", ""))
        registered_scripts.add(script)

        if hook.get("path_base") != "CLAUDE_PROJECT_DIR":
            problems.append(f"{hook_id}: path_base must be CLAUDE_PROJECT_DIR")
        if hook.get("interpreter") != "python":
            problems.append(f"{hook_id}: interpreter must be python")
        if PROJECT_DIR_TOKEN not in command:
            problems.append(f"{hook_id}: command must use {PROJECT_DIR_TOKEN}")
        if not script:
            problems.append(f"{hook_id}: missing script")
        elif not (project / script).exists():
            problems.append(f"{hook_id}: missing script {script}")
        command_script = _command_script(command)
        if script and command_script and command_script != script:
            problems.append(
                f"{hook_id}: command script {command_script} does not match manifest script {script}"
            )

    known_uncovered = set(_string_list(manifest.get("known_uncovered_wired_hooks")))
    settings_path = project / ".claude" / "settings.local.json"
    problems.extend(_local_settings_problems(settings_path))
    wired_hooks = _wired_hooks(settings_path)
    for wired in wired_hooks:
        command = wired["command"]
        script = wired["script"]
        if script and PROJECT_DIR_TOKEN not in command:
            problems.append(
                f"wired hook {wired['event']}:{wired['matcher']} uses non-portable command {command!r}"
            )
        if script and script not in registered_scripts and script not in known_uncovered and command not in known_uncovered:
            problems.append(
                f"wired hook {wired['event']}:{wired['matcher']} script {script} is not in hook_registry or known_uncovered_wired_hooks"
            )

    return problems


def validate_project(project: Path | str = ROOT) -> list[str]:
    project = Path(project)
    return validate_manifest(project, project / DEFAULT_MANIFEST)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)

    manifest_path = args.manifest or (args.project / DEFAULT_MANIFEST)
    problems = validate_manifest(args.project, manifest_path)
    if problems:
        print("Harness manifest check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print("Harness manifest check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
