from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OPERATIONAL_FILES = [
    ROOT / ".agents" / "workflows" / "sync-workflow.md",
    ROOT / "AGENTS.md",
    ROOT / "GEMINI.md",
    ROOT / "README.md",
    ROOT / "README.ko.md",
    ROOT / "docs" / "hooks_reference.md",
    ROOT / "docs" / "orchestration_protocol.md",
    ROOT / "docs" / "workflow_diagrams.md",
    ROOT / "docs" / "workflow_overview.md",
    ROOT / "docs" / "run_templates" / "research_run_packet_template.md",
    ROOT / "docs" / "run_templates" / "run_readme_template.md",
    ROOT / "scripts" / "init_research_project.py",
    ROOT / "scripts" / "run_baseline_validation.py",
]

REFERENCE_PATTERN = re.compile(
    r"(skills/[A-Za-z0-9_.-]+/SKILL\.md|docs/run_templates/[A-Za-z0-9_.-]+\.md)"
)

FORBIDDEN_CURRENT_CARTOGRAPHER_TERMS = [
    "Cartographer (hook-driven, not spawned)",
    "Cartographer Hook",
    "Cartographer Update Events",
    "cartographer_update_template.md",
    "skills/cartographer-update/SKILL.md",
]


def test_operational_docs_reference_existing_skills_and_templates():
    missing = []
    for doc in OPERATIONAL_FILES:
        text = doc.read_text(encoding="utf-8")
        for match in REFERENCE_PATTERN.finditer(text):
            target = ROOT / match.group(1)
            if not target.exists():
                missing.append(f"{doc.relative_to(ROOT)} -> {match.group(1)}")

    assert missing == []


def test_operational_docs_do_not_describe_cartographer_as_current_runtime():
    stale = []
    for doc in OPERATIONAL_FILES:
        text = doc.read_text(encoding="utf-8")
        for term in FORBIDDEN_CURRENT_CARTOGRAPHER_TERMS:
            if term in text:
                stale.append(f"{doc.relative_to(ROOT)} contains {term!r}")

    assert stale == []
