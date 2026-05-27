from pathlib import Path
import importlib.util
import hashlib
import json


def load_installer():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("install_harness", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_source_tree(root: Path) -> None:
    for directory in [
        "skills/example",
        "docs/run_templates",
        "docs/harness",
        "docs/literature",
        "scripts",
        ".claude/agents",
        "outputs",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for file_name in ["AGENTS.md", "GEMINI.md", "PHYSICS.md"]:
        (root / file_name).write_text(f"{file_name}\n", encoding="utf-8")
    (root / "skills/example/SKILL.md").write_text("skill\n", encoding="utf-8")
    (root / "docs/run_templates/template.md").write_text("template\n", encoding="utf-8")
    (root / "docs/hooks_reference.md").write_text("hooks\n", encoding="utf-8")
    (root / "docs/orchestration_protocol.md").write_text("orchestration\n", encoding="utf-8")
    (root / "docs/harness/owned_paths.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "owned": [
                    "scripts/**/*.py",
                    "skills/**",
                    ".claude/agents/**",
                    "AGENTS.md",
                    "GEMINI.md",
                    "PHYSICS.md",
                    "docs/run_templates/**",
                    "docs/hooks_reference.md",
                    "docs/orchestration_protocol.md",
                    "docs/harness/**",
                    "docs/literature/*_template.md",
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "docs/literature/replanning_memo_template.md").write_text("memo\n", encoding="utf-8")
    (root / "scripts/init_research_project.py").write_text("print('run')\n", encoding="utf-8")
    (root / ".claude/agents/implementation-agent.md").write_text("agent\n", encoding="utf-8")
    (root / "outputs/generated.txt").write_text("do not copy\n", encoding="utf-8")


def test_install_from_source_copies_harness_files_only(tmp_path):
    installer = load_installer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    make_source_tree(source)
    target.mkdir()
    (target / "research_code.py").write_text("print('keep')\n", encoding="utf-8")

    installed = installer.install_from_source(source, target, force=False)

    assert installed == [
        ".claude/agents/implementation-agent.md",
        "AGENTS.md",
        "GEMINI.md",
        "PHYSICS.md",
        "docs/harness/owned_paths.json",
        "docs/hooks_reference.md",
        "docs/literature/replanning_memo_template.md",
        "docs/orchestration_protocol.md",
        "docs/run_templates/template.md",
        "scripts/init_research_project.py",
        "skills/example/SKILL.md",
    ]
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "AGENTS.md\n"
    assert (target / "skills/example/SKILL.md").exists()
    assert (target / "docs/run_templates/template.md").exists()
    assert (target / "scripts/init_research_project.py").exists()
    assert (target / ".claude/agents/implementation-agent.md").exists()
    assert (target / "research_code.py").read_text(encoding="utf-8") == "print('keep')\n"
    assert not (target / "outputs/generated.txt").exists()
    assert (target / "harness.lock.json").exists()


def test_install_from_source_refuses_existing_managed_files_without_force(tmp_path):
    installer = load_installer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    make_source_tree(source)
    target.mkdir()
    (target / "AGENTS.md").write_text("existing\n", encoding="utf-8")

    try:
        installer.install_from_source(source, target, force=False)
    except FileExistsError as exc:
        assert "AGENTS.md" in str(exc)
    else:
        raise AssertionError("expected existing managed file to be refused")


def test_install_from_source_overwrites_existing_managed_files_with_force(tmp_path):
    installer = load_installer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    make_source_tree(source)
    target.mkdir()
    (target / "AGENTS.md").write_text("existing\n", encoding="utf-8")

    installer.install_from_source(source, target, force=True)

    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "AGENTS.md\n"


def test_install_writes_lockfile_hashes_for_installed_files(tmp_path):
    installer = load_installer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    make_source_tree(source)

    installer.install_from_source(source, target, force=False)

    lock = json.loads((target / "harness.lock.json").read_text(encoding="utf-8"))
    assert lock["lock_schema"] == 1
    assert lock["harness_version"] is None
    assert "installed_at" in lock
    assert "updated_at" in lock
    for rel_path, digest in lock["files"].items():
        data = (target / rel_path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest


def test_force_install_preserves_project_owned_docs(tmp_path):
    installer = load_installer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    make_source_tree(source)
    target.mkdir()
    (target / "docs" / "gates").mkdir(parents=True)
    (target / "docs" / "plan").mkdir(parents=True)
    (target / "docs" / "process").mkdir(parents=True)
    (target / "docs" / "gates" / "orient_note.md").write_text("research gate\n", encoding="utf-8")
    (target / "docs" / "plan" / "model_spec.md").write_text("research plan\n", encoding="utf-8")
    (target / "docs" / "process" / "live_workflow_diagram.md").write_text("research process\n", encoding="utf-8")
    (target / "AGENTS.md").write_text("old\n", encoding="utf-8")

    installer.install_from_source(source, target, force=True)

    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "AGENTS.md\n"
    assert (target / "docs" / "gates" / "orient_note.md").read_text(encoding="utf-8") == "research gate\n"
    assert (target / "docs" / "plan" / "model_spec.md").read_text(encoding="utf-8") == "research plan\n"
    assert (
        (target / "docs" / "process" / "live_workflow_diagram.md").read_text(encoding="utf-8")
        == "research process\n"
    )
