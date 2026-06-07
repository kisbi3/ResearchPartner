from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, rel_path: str):
    module_path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_layout():
    return _load_module("_layout", ".harness/scripts/_layout.py")


def _load_scaffold_domain():
    return _load_module("scaffold_domain", ".harness/scripts/scaffold_domain.py")


def _load_sync_workflow():
    return _load_module("sync_workflow", ".harness/scripts/sync_workflow.py")


def _mark_project(project: Path) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / ".research-harness").write_text("marker\n", encoding="utf-8")


def test_flat_project_resolves_to_default_domain_and_keeps_layout_v3(tmp_path):
    layout = _load_layout()
    project = tmp_path / "flat"
    project.mkdir()

    assert layout.LAYOUT_VERSION == "3"
    assert layout.domains_root(project) == project / "domains"
    assert layout.domain_names(project) == []
    assert layout.domains(project) == [project]

    assert layout.src_dir(project) == project / "src"
    assert layout.outputs_dir(project) == project / "outputs"
    assert layout.claims_dir(project) == project / "docs" / "claims"


def test_domain_names_and_roots_ignore_files_and_dot_directories(tmp_path):
    layout = _load_layout()
    project = tmp_path / "with-domains"
    (project / "domains" / "b").mkdir(parents=True)
    (project / "domains" / "a").mkdir(parents=True)
    (project / "domains" / ".draft").mkdir(parents=True)
    (project / "domains" / "README.md").write_text("not a domain\n", encoding="utf-8")

    assert layout.domain_names(project) == ["a", "b"]
    assert layout.domains(project) == [
        project / "domains" / "a",
        project / "domains" / "b",
    ]


def test_domain_accessors_are_domain_root_relative(tmp_path):
    layout = _load_layout()
    domain_root = tmp_path / "project" / "domains" / "thread-a"

    assert layout.domain_src_dir(domain_root) == domain_root / "src"
    assert layout.domain_outputs_dir(domain_root) == domain_root / "outputs"
    assert layout.domain_figures_dir(domain_root) == domain_root / "outputs" / "figures"
    assert layout.domain_data_dir(domain_root) == domain_root / "outputs" / "data"
    assert layout.domain_tables_dir(domain_root) == domain_root / "outputs" / "tables"
    assert layout.domain_plan_dir(domain_root) == domain_root / "plan"
    assert layout.domain_claims_dir(domain_root) == domain_root / "claims"
    assert layout.domain_manual(domain_root) == domain_root / "README.md"


def test_scaffold_domain_creates_tree_and_typed_manual(tmp_path):
    scaffold_domain = _load_scaffold_domain()
    project = tmp_path / "project"
    _mark_project(project)

    rc = scaffold_domain.main([
        "--project", str(project),
        "--name", "paper-repro",
        "--type", "reproduction",
    ])

    domain_root = project / "domains" / "paper-repro"
    assert rc == 0
    assert (domain_root / "src").is_dir()
    assert (domain_root / "outputs" / "figures").is_dir()
    assert (domain_root / "outputs" / "data").is_dir()
    assert (domain_root / "outputs" / "tables").is_dir()
    assert (domain_root / "plan").is_dir()
    assert (domain_root / "claims").is_dir()
    manual = (domain_root / "README.md").read_text(encoding="utf-8")
    assert "type: reproduction" in manual
    assert "ground-truth:" in manual
    assert "pass-fail:" in manual
    assert "claim-ceiling-cap:" in manual


def test_scaffold_domain_is_idempotent_and_does_not_overwrite_manual(tmp_path):
    scaffold_domain = _load_scaffold_domain()
    project = tmp_path / "project"
    _mark_project(project)
    args = ["--project", str(project), "--name", "thread-a", "--type", "thread"]

    assert scaffold_domain.main(args) == 0
    manual = project / "domains" / "thread-a" / "README.md"
    manual.write_text("# Custom manual\n", encoding="utf-8")

    assert scaffold_domain.main(args) == 0
    assert manual.read_text(encoding="utf-8") == "# Custom manual\n"


def test_scaffold_domain_default_project_walks_to_nearest_marker(tmp_path, monkeypatch):
    scaffold_domain = _load_scaffold_domain()
    project = tmp_path / "project"
    _mark_project(project)
    nested = project / "src" / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert scaffold_domain.main(["--name", "local-thread", "--type", "subproblem"]) == 0
    assert (project / "domains" / "local-thread" / "README.md").exists()


def test_scaffold_domain_requires_existing_harness_marker(tmp_path, capsys):
    scaffold_domain = _load_scaffold_domain()
    project = tmp_path / "not-a-project"
    project.mkdir()

    rc = scaffold_domain.main([
        "--project", str(project),
        "--name", "thread-a",
        "--type", "thread",
    ])

    captured = capsys.readouterr()
    assert rc != 0
    assert ".research-harness" in captured.err


def test_scaffold_domain_rejects_unknown_type(tmp_path, capsys):
    scaffold_domain = _load_scaffold_domain()
    project = tmp_path / "project"
    _mark_project(project)

    rc = scaffold_domain.main([
        "--project", str(project),
        "--name", "thread-a",
        "--type", "misc",
    ])

    captured = capsys.readouterr()
    assert rc != 0
    assert "Invalid domain type" in captured.err


def test_sync_workflow_surfaces_domains_without_graph_refactor(tmp_path):
    scaffold_domain = _load_scaffold_domain()
    sync_workflow = _load_sync_workflow()
    project = tmp_path / "project"
    _mark_project(project)

    assert scaffold_domain.main([
        "--project", str(project),
        "--name", "b-thread",
        "--type", "thread",
    ]) == 0
    assert scaffold_domain.main([
        "--project", str(project),
        "--name", "a-repro",
        "--type", "reproduction",
    ]) == 0

    out = sync_workflow.sync(project)

    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["domains"] == [
        {
            "name": "a-repro",
            "path": "domains/a-repro",
            "manual": "domains/a-repro/README.md",
            "type": "reproduction",
        },
        {
            "name": "b-thread",
            "path": "domains/b-thread",
            "manual": "domains/b-thread/README.md",
            "type": "thread",
        },
    ]
