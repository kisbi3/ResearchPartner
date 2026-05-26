from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_init_module():
    module_path = ROOT / "scripts" / "init_research_project.py"
    spec = importlib.util.spec_from_file_location("init_research_project", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hook_commands(settings: dict) -> list[str]:
    commands: list[str] = []
    for event_blocks in settings.get("hooks", {}).values():
        for block in event_blocks:
            for hook in block.get("hooks", []):
                command = hook.get("command")
                if command:
                    commands.append(command)
    return commands


def test_init_project_writes_project_dir_based_hook_commands(tmp_path):
    init = load_init_module()
    project = tmp_path / "project"

    init.scaffold_project(project)

    settings = json.loads((project / ".claude" / "settings.local.json").read_text())
    commands = _hook_commands(settings)
    assert commands
    assert all('$CLAUDE_PROJECT_DIR/scripts/' in command for command in commands)
    assert not any(command.startswith("python scripts/") for command in commands)
