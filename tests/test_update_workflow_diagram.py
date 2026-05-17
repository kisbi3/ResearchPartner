import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update_workflow_diagram.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_workflow_diagram", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["update_workflow_diagram"] = module
    spec.loader.exec_module(module)
    return module


BASE_DIAGRAM = (
    "# Live Workflow\n\n"
    "## Active Step\n\n"
    "- Current step: pending\n"
    "- Current owner: pending\n"
    "- Last update: pending\n\n"
    "## Gate Status\n\n"
    "| Gate | Status | Note |\n"
    "|---|---|---|\n"
    "| Test-design seed | pending |  |\n\n"
    "## Evidence Links\n\n"
    "- `docs/research_plan.md`\n\n"
    "## Real-Time Event Log\n\n"
)


def make_diagram(tmp_path: Path) -> Path:
    diagram = tmp_path / "live_workflow_diagram.md"
    diagram.write_text(BASE_DIAGRAM, encoding="utf-8")
    return diagram


def test_spawn_event_adds_in_flight_row(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    rc = module.main([
        "--event", "spawn",
        "--step", "Reproduce Fig 4 of Guo 2026",
        "--agent", "graduate-student",
        "--task-id", "task-3-reproduce-guo",
        "--evidence-record", "docs/gates/seed_design.md#task-3",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    text = diagram.read_text(encoding="utf-8")
    assert "## In-Flight Tasks" in text
    assert "`task-3-reproduce-guo`" in text
    assert "graduate-student" in text
    assert "Reproduce Fig 4 of Guo 2026" in text
    assert "docs/gates/seed_design.md#task-3" in text
    assert "`spawned`" in text


def test_spawn_event_requires_task_id(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    rc = module.main([
        "--event", "spawn",
        "--step", "Reproduce Fig 4",
        "--agent", "graduate-student",
        "--diagram", str(diagram),
    ])
    assert rc == 2


def test_complete_event_marks_in_flight_acknowledged(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    module.main([
        "--event", "spawn",
        "--step", "Run scan",
        "--agent", "graduate-student",
        "--task-id", "task-5-scan",
        "--diagram", str(diagram),
    ])
    rc = module.main([
        "--event", "complete",
        "--step", "Run scan",
        "--agent", "graduate-student",
        "--task-id", "task-5-scan",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    text = diagram.read_text(encoding="utf-8")
    assert "`task-5-scan`" in text
    assert "`acknowledged`" in text
    assert "`spawned` |" not in text.split("## Real-Time Event Log")[0]


def test_resume_with_abandon_marks_in_flight_abandoned(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    module.main([
        "--event", "spawn",
        "--step", "Reproduce Fig 4",
        "--agent", "graduate-student",
        "--task-id", "task-3-reproduce-guo",
        "--diagram", str(diagram),
    ])
    rc = module.main([
        "--event", "resume",
        "--step", "Session resumed after usage limit",
        "--agent", "professor-orchestrator",
        "--task-id", "task-3-reproduce-guo",
        "--resume-decision", "abandon",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    text = diagram.read_text(encoding="utf-8")
    in_flight_section = text.split("## Real-Time Event Log")[0]
    assert "`abandoned`" in in_flight_section
    assert "`spawned` |" not in in_flight_section


def test_resume_without_task_id_only_appends_event(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    rc = module.main([
        "--event", "resume",
        "--step", "Session resumed",
        "--agent", "professor-orchestrator",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    text = diagram.read_text(encoding="utf-8")
    assert "## In-Flight Tasks" not in text  # no rows, no section created
    assert "| `resume` |" in text or "`resume`" in text  # event logged


def test_resume_continue_decision_keeps_task_spawned(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    module.main([
        "--event", "spawn",
        "--step", "Reproduce baseline",
        "--agent", "graduate-student",
        "--task-id", "task-1-baseline",
        "--diagram", str(diagram),
    ])
    rc = module.main([
        "--event", "resume",
        "--step", "Resumed; sub-agent still running",
        "--agent", "professor-orchestrator",
        "--task-id", "task-1-baseline",
        "--resume-decision", "continue",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    text = diagram.read_text(encoding="utf-8")
    in_flight_section = text.split("## Real-Time Event Log")[0]
    assert "`spawned`" in in_flight_section
    assert "`abandoned`" not in in_flight_section


def test_complete_with_unknown_task_id_warns_but_succeeds(tmp_path, capsys):
    module = load_module()
    diagram = make_diagram(tmp_path)
    rc = module.main([
        "--event", "complete",
        "--step", "Unrelated step",
        "--agent", "graduate-student",
        "--task-id", "task-never-spawned",
        "--diagram", str(diagram),
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "no in-flight row" in captured.err


def test_multiple_spawn_events_create_multiple_rows(tmp_path):
    module = load_module()
    diagram = make_diagram(tmp_path)
    for idx in range(3):
        module.main([
            "--event", "spawn",
            "--step", f"Task {idx}",
            "--agent", "graduate-student",
            "--task-id", f"task-{idx}",
            "--diagram", str(diagram),
        ])
    text = diagram.read_text(encoding="utf-8")
    assert "`task-0`" in text
    assert "`task-1`" in text
    assert "`task-2`" in text
    in_flight_section = text.split("## Real-Time Event Log")[0]
    # Three rows in `spawned` state (count the table-cell pattern, not the
    # header comment which also mentions "`spawned`").
    assert in_flight_section.count("| `spawned` |") == 3
