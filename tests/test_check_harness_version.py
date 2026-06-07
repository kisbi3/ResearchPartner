from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    module_path = ROOT / ".harness" / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("install_harness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_checker():
    module_path = ROOT / ".harness" / "scripts" / "check_harness_version.py"
    spec = importlib.util.spec_from_file_location("check_harness_version", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_source_tree(root: Path) -> None:
    for directory in [".harness/scripts", "skills/example", "docs/harness", "docs/run_templates", ".claude/agents"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for file_name in ["AGENTS.md", "GEMINI.md", "PHYSICS.md"]:
        (root / file_name).write_text(f"{file_name}\n", encoding="utf-8")
    (root / ".harness/scripts/tool.py").write_text("print('tool')\n", encoding="utf-8")
    (root / "skills/example/SKILL.md").write_text("skill\n", encoding="utf-8")
    (root / ".claude/agents/implementation-agent.md").write_text("agent\n", encoding="utf-8")
    (root / "docs/run_templates/template.md").write_text("template\n", encoding="utf-8")
    (root / "docs/hooks_reference.md").write_text("hooks\n", encoding="utf-8")
    (root / "docs/orchestration_protocol.md").write_text("orchestration\n", encoding="utf-8")
    (root / "docs/harness/owned_paths.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "owned": [
                    ".harness/scripts/**/*.py",
                    "skills/**/*",
                    ".claude/agents/**/*",
                    "AGENTS.md",
                    "GEMINI.md",
                    "PHYSICS.md",
                    "docs/run_templates/**/*",
                    "docs/hooks_reference.md",
                    "docs/orchestration_protocol.md",
                    "docs/harness/**/*",
                    "docs/literature/*_template.md",
                    "docs/literature/paper_request_queue.md",
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "docs/literature").mkdir(parents=True, exist_ok=True)
    (root / "docs/literature/paper_request_queue.md").write_text("queue\n", encoding="utf-8")


def test_unstamped_project_reports_not_stamped_and_exits_zero(tmp_path, capsys):
    checker = load_checker()
    project = tmp_path / "legacy"
    project.mkdir()

    assert checker.main(["--project", str(project)]) == 0

    captured = capsys.readouterr()
    assert "not stamped" in captured.out


def test_stamped_unmodified_project_reports_zero_local_modifications(tmp_path, capsys):
    installer = load_installer()
    checker = load_checker()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    installer.install_from_source(source, project)

    assert checker.main(["--project", str(project)]) == 0

    captured = capsys.readouterr()
    assert "local modifications: 0" in captured.out


def test_stamped_project_reports_modified_owned_file_and_exits_zero(tmp_path, capsys):
    installer = load_installer()
    checker = load_checker()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    installer.install_from_source(source, project)
    (project / "AGENTS.md").write_text("local edit\n", encoding="utf-8")

    assert checker.main(["--project", str(project)]) == 0

    captured = capsys.readouterr()
    assert "local modifications: 1" in captured.out
    assert "AGENTS.md" in captured.out


def test_malformed_lockfile_is_nonzero(tmp_path, capsys):
    checker = load_checker()
    project = tmp_path / "project"
    project.mkdir()
    (project / "harness.lock.json").write_text("{bad json", encoding="utf-8")

    assert checker.main(["--project", str(project)]) != 0

    captured = capsys.readouterr()
    assert "invalid harness.lock.json" in captured.err
