#!/usr/bin/env python3
"""Validate role agent definitions against the spawn contract registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACTS = Path("docs/harness/spawn_contracts.json")
REQUIRED_ROLES = {
    "graduate-student",
    "code-reviewer",
    "scientific-validator",
    "cache-log-auditor",
    "workflow-manager",
    "peer-review-professor",
}
# graduate-student is now a spawned leaf agent (Model-A lab), so it is no longer
# a forbidden agent file. The Lead Agent (professor) remains the only spawner.
FORBIDDEN_AGENT_FILES: dict[str, str] = {}
DESCRIPTION_PREFIX = "Explicitly spawned only"
DESCRIPTION_FORBIDDEN_PHRASES = (
    "use this agent when",
    "trigger when",
    "examples:",
    "<example>",
)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def _resolve(project: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project / path


def _parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw = parts[1]
    body = parts[2]
    data: dict[str, Any] = {}
    current_key = ""
    for raw_line in raw.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(line[4:].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        data[current_key] = _parse_frontmatter_value(value.strip())
    return data, body


def _parse_frontmatter_value(value: str) -> Any:
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    return value.strip().strip("\"'")


def _frontmatter_tools(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _declared_skill_spawns(skill_path: Path) -> list[str]:
    if not skill_path.exists():
        return []
    text = skill_path.read_text(encoding="utf-8")
    marker = "Canonical spawn subagent types:"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1]
    heading_match = re.search(r"\n## ", section)
    if heading_match:
        section = section[: heading_match.start()]
    return re.findall(r"`([a-z0-9-]+)`", section)


def _format_set(values: set[str]) -> str:
    return ", ".join(sorted(values)) if values else "<none>"


def validate_contracts(project: Path | str, contracts_path: Path | str) -> list[str]:
    project = Path(project)
    contracts_path = Path(contracts_path)
    problems: list[str] = []

    if not contracts_path.exists():
        return [f"missing spawn contracts: {contracts_path}"]
    try:
        data = _load_json(contracts_path)
    except ValueError as exc:
        return [str(exc)]

    if data.get("schema_version") != 1:
        problems.append("schema_version must be 1")

    for forbidden, reason in FORBIDDEN_AGENT_FILES.items():
        if (project / forbidden).exists():
            problems.append(f"forbidden agent file {forbidden}: {reason}")

    contracts = data.get("contracts")
    if not isinstance(contracts, list):
        return problems + ["contracts must be a list"]

    roles: set[str] = set()
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            problems.append(f"contracts[{index}] must be an object")
            continue
        role = str(contract.get("role", "")).strip()
        if not role:
            problems.append(f"contracts[{index}] missing role")
            continue
        if role in roles:
            problems.append(f"duplicate role: {role}")
        roles.add(role)

        skill = str(contract.get("skill", "")).strip()
        skill_path = _resolve(project, skill) if skill else Path()
        if not skill:
            problems.append(f"{role}: missing skill")
        elif not skill_path.exists():
            problems.append(f"{role}: missing skill {skill}")

        allowed_tools = _string_list(contract.get("allowed_tools"))
        if not allowed_tools:
            problems.append(f"{role}: allowed_tools must be a non-empty string list")
        if "Agent" in allowed_tools:
            problems.append(f"{role}: Agent tool is reserved for the Lead Agent; role agents are leaf agents")

        allowed_spawns = _string_list(contract.get("allowed_spawn_subagent_types"))
        if allowed_spawns:
            problems.append(f"{role}: leaf roles must not declare child spawns")

        declared_spawns = _declared_skill_spawns(skill_path)
        if set(declared_spawns) != set(allowed_spawns):
            problems.append(
                f"{role}: allowed_spawn_subagent_types {_format_set(set(allowed_spawns))} "
                f"does not match skill declarations {_format_set(set(declared_spawns))}"
            )

        agent_file = str(contract.get("agent_file", "")).strip()
        agent_path = _resolve(project, agent_file) if agent_file else Path()
        if not agent_file:
            problems.append(f"{role}: missing agent_file")
            continue
        if not agent_path.exists():
            problems.append(f"{role}: missing agent file {agent_file}")
            continue

        frontmatter, body = _parse_frontmatter(agent_path)
        name = str(frontmatter.get("name", "")).strip()
        if name != role:
            problems.append(f"{role}: frontmatter name {name!r} must equal subagent_type {role!r}")

        description = str(frontmatter.get("description", "")).strip()
        if not description.startswith(DESCRIPTION_PREFIX):
            problems.append(f"{role}: description must start with {DESCRIPTION_PREFIX!r}")
        lowered = description.lower()
        for phrase in DESCRIPTION_FORBIDDEN_PHRASES:
            if phrase in lowered:
                problems.append(f"{role}: description contains forbidden phrase {phrase!r}")

        actual_tools = _frontmatter_tools(frontmatter.get("tools"))
        if set(actual_tools) != set(allowed_tools):
            problems.append(
                f"{role}: frontmatter tools {_format_set(set(actual_tools))} "
                f"do not match allowed_tools {_format_set(set(allowed_tools))}"
            )

        if skill and f"Load {skill}" not in body:
            problems.append(f"{role}: agent body must delegate to {skill}")

    missing_roles = REQUIRED_ROLES - roles
    for role in sorted(missing_roles):
        problems.append(f"missing required role: {role}")

    extra_roles = roles - REQUIRED_ROLES
    for role in sorted(extra_roles):
        problems.append(f"unknown role: {role}")

    protocol = project / "docs" / "orchestration_protocol.md"
    if protocol.exists():
        text = protocol.read_text(encoding="utf-8")
        for role in sorted(REQUIRED_ROLES):
            if f"subagent_type: {role}" not in text:
                problems.append(f"orchestration_protocol.md missing subagent_type: {role}")

    return problems


def validate_project(project: Path | str = ROOT) -> list[str]:
    project = Path(project)
    return validate_contracts(project, project / DEFAULT_CONTRACTS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--contracts", type=Path)
    args = parser.parse_args(argv)

    contracts_path = args.contracts or (args.project / DEFAULT_CONTRACTS)
    problems = validate_contracts(args.project, contracts_path)
    if problems:
        print("Spawn contract check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print("Spawn contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
