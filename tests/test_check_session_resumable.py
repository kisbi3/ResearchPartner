import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".harness" / "scripts" / "check_session_resumable.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_session_resumable", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["check_session_resumable"] = module
    spec.loader.exec_module(module)
    return module


def make_run(tmp_path: Path, diagram_body: str) -> Path:
    run = tmp_path / "2026-05-17-fixture-run"
    diagram_path = run / "docs" / "process" / "live_workflow_diagram.md"
    diagram_path.parent.mkdir(parents=True)
    diagram_path.write_text(diagram_body, encoding="utf-8")
    return run


CLEAN_DIAGRAM = (
    "# Live Workflow\n\n"
    "## Active Step\n\n"
    "- Current step: **Retrospect**\n"
    "- Current owner: professor-orchestrator\n"
    "- Last update: 2026-05-17 12:00 UTC\n\n"
    "## Gate Status\n\n"
    "| Gate | Status | Note |\n"
    "|---|---|---|\n"
    "| Professor interview | `pass` ✓ |  |\n"
    "| Test-design seed | `pass` ✓ |  |\n\n"
    "## In-Flight Tasks\n\n"
    "| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n"
    "|---|---|---|---|---|---|\n"
    "| `task-1-baseline` | graduate-student | 2026-05-17 09:00 UTC | Baseline | docs/gates/seed_design.md | `acknowledged` |\n"
    "\n## Real-Time Event Log\n\n"
)


DIRTY_DIAGRAM = (
    "# Live Workflow\n\n"
    "## Active Step\n\n"
    "- Current step: **Execute**\n"
    "- Current owner: graduate-student\n"
    "- Last update: 2026-05-17 09:30 UTC\n\n"
    "## Gate Status\n\n"
    "| Gate | Status | Note |\n"
    "|---|---|---|\n"
    "| Professor interview | `pass` ✓ |  |\n"
    "| Test-design seed | `in_progress` 🔄 |  |\n"
    "| Baseline | `blocked` ⛔ | waiting for researcher |\n\n"
    "## In-Flight Tasks\n\n"
    "| Task ID | Sub-agent | Spawned (UTC) | Step | Evidence Record | Status |\n"
    "|---|---|---|---|---|---|\n"
    "| `task-3-reproduce-guo` | graduate-student | 2026-05-17 09:22 UTC | Reproduce Fig 4 | docs/gates/seed_design.md#task-3 | `spawned` |\n"
    "| `task-5-scan` | graduate-student | 2026-05-17 09:48 UTC | Scan ε grid | docs/gates/seed_design.md#task-5 | `spawned` |\n"
    "\n## Real-Time Event Log\n\n"
)


def test_clean_diagram_passes(tmp_path):
    module = load_module()
    run = make_run(tmp_path, CLEAN_DIAGRAM)
    code, report = module.check_run(run)
    assert code == 0
    assert report["resumable"] is True
    assert report["in_flight_tasks"] == []
    assert report["blocking_gates"] == []
    assert report["active_step"]["current_step"] == "Retrospect"


def test_in_flight_tasks_fail(tmp_path):
    module = load_module()
    run = make_run(tmp_path, DIRTY_DIAGRAM)
    code, report = module.check_run(run)
    assert code == 1
    assert report["resumable"] is False
    task_ids = {t["task_id"] for t in report["in_flight_tasks"]}
    assert task_ids == {"task-3-reproduce-guo", "task-5-scan"}


def test_blocking_gates_reported(tmp_path):
    module = load_module()
    run = make_run(tmp_path, DIRTY_DIAGRAM)
    _, report = module.check_run(run)
    gate_names = {g["name"] for g in report["blocking_gates"]}
    assert gate_names == {"Test-design seed", "Baseline"}
    statuses = {g["status"] for g in report["blocking_gates"]}
    assert statuses == {"in_progress", "blocked"}


def test_missing_diagram_fails(tmp_path):
    module = load_module()
    run = tmp_path / "empty-run"
    run.mkdir()
    code, report = module.check_run(run)
    assert code == 1
    assert report["resumable"] is False
    assert "not found" in report["reason"]


def test_json_cli_output_is_valid_json(tmp_path, capsys):
    module = load_module()
    run = make_run(tmp_path, CLEAN_DIAGRAM)
    code = module.main(["--run", str(run), "--json"])
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["resumable"] is True
    assert code == 0


def test_plain_text_cli_lists_in_flight_tasks(tmp_path, capsys):
    module = load_module()
    run = make_run(tmp_path, DIRTY_DIAGRAM)
    code = module.main(["--run", str(run)])
    captured = capsys.readouterr().out
    assert code == 1
    assert "task-3-reproduce-guo" in captured
    assert "task-5-scan" in captured
    assert "Resumable: NO" in captured


def test_legacy_layout_diagram_is_detected(tmp_path):
    module = load_module()
    run = tmp_path / "2026-05-17-legacy"
    legacy = run / "docs" / "live_workflow_diagram.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(CLEAN_DIAGRAM, encoding="utf-8")
    code, report = module.check_run(run)
    assert code == 0
    assert report["diagram"].endswith("live_workflow_diagram.md")


def test_acknowledged_rows_do_not_block_resume(tmp_path):
    module = load_module()
    body = CLEAN_DIAGRAM.replace(
        "| `task-1-baseline` | graduate-student | 2026-05-17 09:00 UTC | Baseline | docs/gates/seed_design.md | `acknowledged` |",
        (
            "| `task-1-baseline` | graduate-student | 2026-05-17 09:00 UTC | Baseline | docs/gates/seed_design.md | `acknowledged` |\n"
            "| `task-2-abandoned` | graduate-student | 2026-05-17 10:00 UTC | Lost task | docs/gates/seed_design.md | `abandoned` |"
        ),
    )
    run = make_run(tmp_path, body)
    code, report = module.check_run(run)
    assert code == 0
    assert report["in_flight_tasks"] == []
