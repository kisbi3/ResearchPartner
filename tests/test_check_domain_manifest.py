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


def _load_scaffold_domain():
    return _load_module("scaffold_domain", ".harness/scripts/scaffold_domain.py")


def _load_check_domain_manifest():
    return _load_module("check_domain_manifest", ".harness/scripts/check_domain_manifest.py")


def _mark_project(project: Path) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / ".research-harness").write_text("marker\n", encoding="utf-8")


def test_no_domains_is_dormant_exit_zero(tmp_path):
    checker = _load_check_domain_manifest()
    project = tmp_path / "flat"
    project.mkdir()

    assert checker.validate_project(project) == []
    assert checker.main(["--project", str(project)]) == 0


def test_scaffolded_domain_manifest_passes(tmp_path):
    scaffold_domain = _load_scaffold_domain()
    checker = _load_check_domain_manifest()
    project = tmp_path / "project"
    _mark_project(project)

    assert scaffold_domain.main([
        "--project", str(project),
        "--name", "paper-repro",
        "--type", "reproduction",
    ]) == 0

    assert checker.validate_project(project) == []
    assert checker.main(["--project", str(project)]) == 0


def test_domain_manifest_missing_readme_exits_two(tmp_path, capsys):
    checker = _load_check_domain_manifest()
    project = tmp_path / "project"
    (project / "domains" / "thread-a").mkdir(parents=True)

    rc = checker.main(["--project", str(project)])

    captured = capsys.readouterr()
    assert rc == 2
    assert "thread-a" in captured.err
    assert "missing README.md" in captured.err


def test_domain_manifest_rejects_invalid_type(tmp_path, capsys):
    checker = _load_check_domain_manifest()
    project = tmp_path / "project"
    domain = project / "domains" / "thread-a"
    domain.mkdir(parents=True)
    (domain / "README.md").write_text(
        "---\n"
        "type: misc\n"
        "purpose: <placeholder>\n"
        "ground-truth: <placeholder>\n"
        "pass-fail: <placeholder>\n"
        "units: <placeholder>\n"
        "assumptions: <placeholder>\n"
        "relations:\n"
        "  depends-on: <placeholder>\n"
        "  integrates-into: <placeholder>\n"
        "claim-ceiling-cap: <placeholder>\n"
        "---\n",
        encoding="utf-8",
    )

    rc = checker.main(["--project", str(project)])

    captured = capsys.readouterr()
    assert rc == 2
    assert "invalid type" in captured.err
    assert "misc" in captured.err


def test_domain_manifest_rejects_missing_required_field(tmp_path, capsys):
    checker = _load_check_domain_manifest()
    project = tmp_path / "project"
    domain = project / "domains" / "thread-a"
    domain.mkdir(parents=True)
    (domain / "README.md").write_text(
        "---\n"
        "type: thread\n"
        "purpose: <placeholder>\n"
        "ground-truth: <placeholder>\n"
        "pass-fail: <placeholder>\n"
        "units: <placeholder>\n"
        "assumptions: <placeholder>\n"
        "relations:\n"
        "  depends-on: <placeholder>\n"
        "---\n",
        encoding="utf-8",
    )

    rc = checker.main(["--project", str(project)])

    captured = capsys.readouterr()
    assert rc == 2
    assert "missing required field" in captured.err
    assert "integrates-into" in captured.err
