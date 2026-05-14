from pathlib import Path
import importlib.util


def load_installer():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("install_harness", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_source_tree(root: Path) -> None:
    for directory in ["skills/example", "docs/run_templates", "scripts", "outputs"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for file_name in ["AGENTS.md", "GEMINI.md", "PHYSICS.md"]:
        (root / file_name).write_text(f"{file_name}\n", encoding="utf-8")
    (root / "skills/example/SKILL.md").write_text("skill\n", encoding="utf-8")
    (root / "docs/run_templates/template.md").write_text("template\n", encoding="utf-8")
    (root / "scripts/start_research_run.py").write_text("print('run')\n", encoding="utf-8")
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
        "AGENTS.md",
        "GEMINI.md",
        "PHYSICS.md",
        "skills/",
        "docs/",
        "scripts/",
    ]
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "AGENTS.md\n"
    assert (target / "skills/example/SKILL.md").exists()
    assert (target / "docs/run_templates/template.md").exists()
    assert (target / "scripts/start_research_run.py").exists()
    assert (target / "research_code.py").read_text(encoding="utf-8") == "print('keep')\n"
    assert not (target / "outputs/generated.txt").exists()


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
