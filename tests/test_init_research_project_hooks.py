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


def test_scaffold_merges_hooks_into_existing_settings(tmp_path):
    """Regression: a project adopted into a repo that already has a
    settings.local.json must still receive the enforcement hooks, and must
    keep the researcher's existing permissions and custom hooks."""
    init = load_init_module()
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    pre = {
        "permissions": {"allow": ["Bash(git status)"]},
        "hooks": {
            "PreToolUse": [
                {"matcher": "Read", "hooks": [{"type": "command", "command": "echo user-hook"}]}
            ]
        },
    }
    (project / ".claude" / "settings.local.json").write_text(json.dumps(pre, indent=2))

    init.scaffold_project(project)

    settings = json.loads((project / ".claude" / "settings.local.json").read_text())
    commands = _hook_commands(settings)
    # Researcher content preserved …
    assert settings["permissions"]["allow"] == ["Bash(git status)"]
    assert "echo user-hook" in commands
    # … and the harness enforcement hooks are now installed.
    assert any("enforce_gate_sequence.py" in c for c in commands)
    assert any("check_src_write_authorization.py" in c for c in commands)
    assert any("check_peer_review_invocation.py" in c for c in commands)


def test_merge_hook_settings_is_idempotent():
    """Re-running init on a project that already has the harness hooks must
    not duplicate any command."""
    init = load_init_module()
    harness = json.loads(init._CLAUDE_SETTINGS_CONTENT)
    merged_once, added_once = init._merge_hook_settings(harness, harness)
    assert added_once == []
    assert _hook_commands(merged_once) == _hook_commands(harness)


def test_scaffold_warns_and_preserves_unparseable_settings(tmp_path, capsys):
    """An existing but unparseable settings.local.json must not be clobbered;
    the user must be warned that hooks were not installed."""
    init = load_init_module()
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    garbage = "{ this is not valid json "
    (project / ".claude" / "settings.local.json").write_text(garbage)

    init.scaffold_project(project)

    # File is preserved verbatim (not clobbered) …
    assert (project / ".claude" / "settings.local.json").read_text() == garbage
    # … and a loud warning was emitted.
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "NOT installed" in err
