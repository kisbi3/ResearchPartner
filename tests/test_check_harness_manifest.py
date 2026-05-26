from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    module_path = ROOT / "scripts" / "check_harness_manifest.py"
    spec = importlib.util.spec_from_file_location("check_harness_manifest", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minimal_manifest(**overrides):
    manifest = {
        "schema_version": 1,
        "capabilities": [
            {
                "id": "orient-gate",
                "title": "Orient Gate",
                "kind": "gate",
                "enforcement": "hard",
                "scripts": ["scripts/check_orient_recorded.py"],
                "docs": ["skills/task-intake/SKILL.md"],
                "workflow_gate_keys": ["orient_gate"],
            }
        ],
        "hook_registry": [
            {
                "id": "contract-sync",
                "event": "Manual",
                "matcher": "Bash",
                "script": "scripts/check_contract_sync.py",
                "command": 'python "$CLAUDE_PROJECT_DIR/scripts/check_contract_sync.py"',
                "path_base": "CLAUDE_PROJECT_DIR",
                "interpreter": "python",
                "enforcement": "hard",
            }
        ],
        "known_uncovered_wired_hooks": [],
    }
    manifest.update(overrides)
    return manifest


def test_repository_manifest_passes():
    checker = load_checker()

    assert checker.validate_project(ROOT) == []


def test_manifest_rejects_guessed_workflow_node_ids(tmp_path):
    checker = load_checker()
    manifest = _minimal_manifest(
        capabilities=[
            {
                "id": "interview-gate",
                "title": "Interview Gate",
                "kind": "gate",
                "enforcement": "hard",
                "scripts": ["scripts/check_interview_recorded.py"],
                "docs": ["skills/professor-interview/SKILL.md"],
                "workflow_gate_keys": ["gate_interview"],
            }
        ]
    )
    manifest_path = tmp_path / "capability_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    problems = checker.validate_manifest(ROOT, manifest_path)

    assert any("workflow_gate_keys" in problem and "gate_interview" in problem for problem in problems)


def test_manifest_requires_project_dir_hook_paths(tmp_path):
    checker = load_checker()
    manifest = _minimal_manifest(
        hook_registry=[
            {
                "id": "bad-hook-path",
                "event": "Manual",
                "matcher": "Bash",
                "script": "scripts/check_contract_sync.py",
                "command": "python scripts/check_contract_sync.py",
                "path_base": "CLAUDE_PROJECT_DIR",
                "interpreter": "python",
                "enforcement": "hard",
            }
        ]
    )
    manifest_path = tmp_path / "capability_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    problems = checker.validate_manifest(ROOT, manifest_path)

    assert any("CLAUDE_PROJECT_DIR" in problem for problem in problems)


def test_wired_hook_missing_from_registry_or_known_uncovered_fails(tmp_path):
    checker = load_checker()
    manifest = json.loads((ROOT / "docs" / "harness" / "capability_manifest.json").read_text())
    manifest["hook_registry"] = [
        hook
        for hook in manifest["hook_registry"]
        if hook["script"] != "scripts/check_spawn_log_integrity.py"
    ]
    manifest["known_uncovered_wired_hooks"] = []
    manifest_path = tmp_path / "capability_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    problems = checker.validate_manifest(ROOT, manifest_path)

    assert any(
        "not in hook_registry" in problem
        and "scripts/check_spawn_log_integrity.py" in problem
        for problem in problems
    )
