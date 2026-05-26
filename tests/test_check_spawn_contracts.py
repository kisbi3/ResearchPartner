from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    module_path = ROOT / "scripts" / "check_spawn_contracts.py"
    spec = importlib.util.spec_from_file_location("check_spawn_contracts", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_spawn_contracts_pass():
    checker = load_checker()

    assert checker.validate_project(ROOT) == []


def test_missing_agent_file_fails(tmp_path):
    checker = load_checker()
    contracts = json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())
    contracts["contracts"][0]["agent_file"] = ".claude/agents/missing-role.md"
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")

    problems = checker.validate_contracts(ROOT, path)

    assert any("missing agent file" in problem for problem in problems)


def test_graduate_student_must_keep_evidence_write_tools(tmp_path):
    checker = load_checker()
    contracts = json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())
    graduate = next(item for item in contracts["contracts"] if item["role"] == "graduate-student")
    graduate["allowed_tools"] = ["Read", "Grep", "Glob", "Agent"]
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")

    problems = checker.validate_contracts(ROOT, path)

    assert any("graduate-student" in problem and "Write" in problem for problem in problems)
    assert any("graduate-student" in problem and "Edit" in problem for problem in problems)


def test_agent_frontmatter_tools_must_match_contract(tmp_path):
    checker = load_checker()
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    agent_file = agent_dir / "graduate-student.md"
    agent_file.write_text(
        """---
name: graduate-student
description: Explicitly spawned only by the Lead Agent for one seed task.
tools: Read, Grep, Glob, Write, Edit, Agent, Bash
---

Load skills/graduate-student/SKILL.md.
""",
        encoding="utf-8",
    )
    contracts = json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())
    graduate = next(item for item in contracts["contracts"] if item["role"] == "graduate-student")
    graduate["agent_file"] = str(agent_file.relative_to(ROOT)) if agent_file.is_relative_to(ROOT) else str(agent_file)
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")

    problems = checker.validate_contracts(ROOT, path)

    assert any("frontmatter tools" in problem and "Bash" in problem for problem in problems)


def test_graduate_student_spawn_set_must_match_skill(tmp_path):
    checker = load_checker()
    contracts = json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())
    graduate = next(item for item in contracts["contracts"] if item["role"] == "graduate-student")
    graduate["allowed_spawn_subagent_types"] = [
        "implementation-agent",
        "scientific-validator",
        "cache-log-auditor",
        "figure-agent",
    ]
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")

    problems = checker.validate_contracts(ROOT, path)

    assert any("allowed_spawn_subagent_types" in problem and "figure-agent" in problem for problem in problems)


def test_description_must_be_explicit_spawn_only(tmp_path):
    checker = load_checker()
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    agent_file = agent_dir / "peer-review-professor.md"
    agent_file.write_text(
        """---
name: peer-review-professor
description: Use this agent when reviewing claims.
tools: Read, Grep, Glob
---

Load skills/peer-review-professor/SKILL.md.
""",
        encoding="utf-8",
    )
    contracts = json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())
    peer = next(item for item in contracts["contracts"] if item["role"] == "peer-review-professor")
    peer["agent_file"] = str(agent_file)
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")

    problems = checker.validate_contracts(ROOT, path)

    assert any("description must start" in problem for problem in problems)
    assert any("description contains forbidden phrase" in problem for problem in problems)
