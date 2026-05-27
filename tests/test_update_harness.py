from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    module_path = ROOT / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("install_harness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_updater():
    module_path = ROOT / "scripts" / "update_harness.py"
    spec = importlib.util.spec_from_file_location("update_harness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source_tree(root: Path) -> None:
    for directory in [
        "scripts",
        "skills/example",
        "docs/harness",
        "docs/run_templates",
        "docs/literature",
        ".claude/agents",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for file_name in ["AGENTS.md", "GEMINI.md", "PHYSICS.md"]:
        (root / file_name).write_text(f"{file_name} v1\n", encoding="utf-8")
    (root / "scripts/tool.py").write_text("print('tool v1')\n", encoding="utf-8")
    (root / "skills/example/SKILL.md").write_text("skill v1\n", encoding="utf-8")
    (root / ".claude/agents/implementation-agent.md").write_text("agent v1\n", encoding="utf-8")
    (root / "docs/run_templates/template.md").write_text("template v1\n", encoding="utf-8")
    (root / "docs/hooks_reference.md").write_text("hooks v1\n", encoding="utf-8")
    (root / "docs/orchestration_protocol.md").write_text("orchestration v1\n", encoding="utf-8")
    (root / "docs/literature/paper_request_queue.md").write_text("queue v1\n", encoding="utf-8")
    (root / "docs/harness/owned_paths.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "owned": [
                    "scripts/**/*.py",
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


def install_project(source: Path, project: Path) -> None:
    installer = load_installer()
    installer.install_from_source(source, project)


def read_lock(project: Path) -> dict:
    return json.loads((project / "harness.lock.json").read_text(encoding="utf-8"))


def test_dry_run_reports_update_without_mutating_disk(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    before_file = (project / "AGENTS.md").read_text(encoding="utf-8")
    before_lock = (project / "harness.lock.json").read_text(encoding="utf-8")
    (source / "AGENTS.md").write_text("AGENTS.md v2\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source)]) == 0

    captured = capsys.readouterr()
    assert "UPDATE: 1" in captured.out
    assert "- AGENTS.md" in captured.out
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == before_file
    assert (project / "harness.lock.json").read_text(encoding="utf-8") == before_lock


def test_apply_updates_unmodified_owned_file_and_lock(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    installed_at = read_lock(project)["installed_at"]
    (source / "AGENTS.md").write_text("AGENTS.md v2\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "UPDATE: 1" in captured.out
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "AGENTS.md v2\n"
    lock = read_lock(project)
    assert lock["installed_at"] == installed_at
    assert lock["files"]["AGENTS.md"] == sha256(source / "AGENTS.md")


def test_conflict_keeps_local_edit_and_writes_harness_new_sidecar(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    (project / "AGENTS.md").write_text("local edit\n", encoding="utf-8")
    (source / "AGENTS.md").write_text("AGENTS.md v2\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "CONFLICT: 1" in captured.out
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "local edit\n"
    assert (project / "AGENTS.md.harness-new").read_text(encoding="utf-8") == "AGENTS.md v2\n"
    assert read_lock(project)["files"]["AGENTS.md"] == sha256(source / "AGENTS.md")


def test_local_edit_is_kept_when_source_matches_lock(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    before_lock = (project / "harness.lock.json").read_text(encoding="utf-8")
    (project / "AGENTS.md").write_text("local edit\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "LOCAL-EDIT-KEPT: 1" in captured.out
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "local edit\n"
    assert (project / "harness.lock.json").read_text(encoding="utf-8") == before_lock


def test_apply_adds_new_owned_source_file_to_project_and_lock(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    (source / "docs/run_templates/new_template.md").write_text("new template\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "ADD: 1" in captured.out
    assert (project / "docs/run_templates/new_template.md").read_text(encoding="utf-8") == "new template\n"
    assert "docs/run_templates/new_template.md" in read_lock(project)["files"]


def test_removed_source_file_is_not_deleted_from_project(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    (source / "docs/run_templates/template.md").unlink()

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "REMOVED: 1" in captured.out
    assert (project / "docs/run_templates/template.md").read_text(encoding="utf-8") == "template v1\n"
    assert "docs/run_templates/template.md" not in read_lock(project)["files"]


def test_user_deleted_locked_file_is_not_recreated(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    before_lock = (project / "harness.lock.json").read_text(encoding="utf-8")
    (project / "AGENTS.md").unlink()

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    captured = capsys.readouterr()
    assert "MISSING-LOCAL: 1" in captured.out
    assert not (project / "AGENTS.md").exists()
    assert (project / "harness.lock.json").read_text(encoding="utf-8") == before_lock


def test_apply_never_touches_paths_outside_owned_or_lock(tmp_path):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    install_project(source, project)
    (project / "outputs").mkdir()
    (project / "docs/plan").mkdir(parents=True)
    (project / "outputs/x").write_text("result\n", encoding="utf-8")
    (project / "docs/plan/model_spec.md").write_text("model spec\n", encoding="utf-8")
    (source / "AGENTS.md").write_text("AGENTS.md v2\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--apply"]) == 0

    assert (project / "outputs/x").read_text(encoding="utf-8") == "result\n"
    assert (project / "docs/plan/model_spec.md").read_text(encoding="utf-8") == "model spec\n"


def test_adopt_stamps_legacy_project_without_updating_files(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    project.mkdir()
    (project / "AGENTS.md").write_text("legacy local\n", encoding="utf-8")
    (project / "scripts").mkdir()
    (project / "scripts/tool.py").write_text("legacy tool\n", encoding="utf-8")

    assert updater.main(["--project", str(project), "--source", str(source), "--adopt"]) == 0

    captured = capsys.readouterr()
    assert "adopted" in captured.out.lower()
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "legacy local\n"
    lock = read_lock(project)
    assert lock["files"]["AGENTS.md"] == sha256(project / "AGENTS.md")
    assert lock["files"]["scripts/tool.py"] == sha256(project / "scripts/tool.py")


def test_missing_lock_without_adopt_is_nonzero(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    project = tmp_path / "project"
    make_source_tree(source)
    project.mkdir()

    assert updater.main(["--project", str(project), "--source", str(source)]) != 0

    captured = capsys.readouterr()
    assert "run --adopt or reinstall" in captured.err


def test_source_equal_to_project_is_refused(tmp_path, capsys):
    updater = load_updater()
    source = tmp_path / "source"
    make_source_tree(source)

    assert updater.main(["--project", str(source), "--source", str(source)]) != 0

    captured = capsys.readouterr()
    assert "source and project must be different" in captured.err
