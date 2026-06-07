from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    module_path = ROOT / ".harness" / "scripts" / "check_spawn_contracts.py"
    spec = importlib.util.spec_from_file_location("check_spawn_contracts", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contracts():
    return json.loads((ROOT / "docs" / "harness" / "spawn_contracts.json").read_text())


def _write_contracts(tmp_path: Path, contracts: dict) -> Path:
    path = tmp_path / "spawn_contracts.json"
    path.write_text(json.dumps(contracts), encoding="utf-8")
    return path


def test_repository_spawn_contracts_pass():
    checker = load_checker()

    assert checker.validate_project(ROOT) == []


def test_unknown_role_and_agent_tool_rejected(tmp_path):
    # graduate-student is now a valid spawned leaf role; an undefined role plus an
    # Agent tool must still be rejected (the Lead Agent is the only spawner).
    checker = load_checker()
    contracts = _contracts()
    contracts["contracts"].append(
        {
            "role": "lab-intern",
            "agent_file": ".claude/agents/lab-intern.md",
            "skill": "skills/lab-intern/SKILL.md",
            "allowed_tools": ["Read", "Grep", "Glob", "Agent"],
            "allowed_spawn_subagent_types": ["graduate-student"],
        }
    )

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("unknown role: lab-intern" in problem for problem in problems)
    assert any("Agent tool is reserved for the Lead Agent" in problem for problem in problems)


def test_missing_leaf_agent_file_fails(tmp_path):
    checker = load_checker()
    contracts = _contracts()
    contracts["contracts"][0]["agent_file"] = ".claude/agents/missing-role.md"

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("missing agent file" in problem for problem in problems)


def test_role_agents_must_not_have_agent_tool(tmp_path):
    checker = load_checker()
    contracts = _contracts()
    graduate = next(item for item in contracts["contracts"] if item["role"] == "graduate-student")
    graduate["allowed_tools"] = ["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Agent"]

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("graduate-student" in problem and "Agent tool is reserved" in problem for problem in problems)


def test_agent_frontmatter_tools_must_match_contract(tmp_path):
    checker = load_checker()
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir()
    agent_file = agent_dir / "code-reviewer.md"
    agent_file.write_text(
        """---
name: code-reviewer
description: Explicitly spawned only by the Lead Agent to statically review code.
tools: Read, Grep, Glob, Bash
---

Load skills/code-reviewer/SKILL.md.
""",
        encoding="utf-8",
    )
    contracts = _contracts()
    reviewer = next(item for item in contracts["contracts"] if item["role"] == "code-reviewer")
    reviewer["agent_file"] = str(agent_file)

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("frontmatter tools" in problem and "Bash" in problem for problem in problems)


def test_leaf_contracts_must_not_allow_child_spawns(tmp_path):
    checker = load_checker()
    contracts = _contracts()
    validator = next(item for item in contracts["contracts"] if item["role"] == "scientific-validator")
    validator["allowed_spawn_subagent_types"] = ["cache-log-auditor"]

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("scientific-validator" in problem and "leaf roles must not declare child spawns" in problem for problem in problems)


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
    contracts = _contracts()
    peer = next(item for item in contracts["contracts"] if item["role"] == "peer-review-professor")
    peer["agent_file"] = str(agent_file)

    problems = checker.validate_contracts(ROOT, _write_contracts(tmp_path, contracts))

    assert any("description must start" in problem for problem in problems)
    assert any("description contains forbidden phrase" in problem for problem in problems)
