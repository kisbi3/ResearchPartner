"""Regression coverage for the Human-Owned Decision Gate (the brake).

The brake is the harness's #1 principle made enforceable: the lab proposes, but
only the researcher (PI) records the decision. These tests cover:

- path_check_hooks.py hard-blocks every agent Write/Edit to a researcher-owned
  decision file (and the skip waivers), but allows the lab's proposal notes.
- The orient/interview/model gate checkers stay closed until the matching
  *_decision.md has a non-empty ## Decision (and honour --project — the
  parse_args(argv) fix).
- The seed gate requires the PI's seed_decision even when the smoke-run bypass
  env var is set: the bypass waives the smoke requirement, never the sign-off.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "proj"
    (p / "docs" / "gates").mkdir(parents=True)
    (p / "docs" / "plan").mkdir(parents=True)
    (p / "docs" / "literature").mkdir(parents=True)
    (p / "src").mkdir(parents=True)
    (p / ".research-harness").write_text("")
    return p


def run_pre_write(project: Path, target: Path, *, env: dict | None = None) -> tuple[int, str]:
    """Invoke path_check_hooks.py 'pre' for a Write to target, cwd=project."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "path_check_hooks.py"), "pre"],
        input=json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(target)}}),
        capture_output=True, text=True, cwd=str(project), env=env,
    )
    return proc.returncode, proc.stderr.strip()


def run_checker(script: str, project: Path, *extra: str, env: dict | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), "--project", str(project), *extra],
        capture_output=True, text=True, env=env,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


# ── The write-block ──────────────────────────────────────────────────────────

class TestDecisionWriteBlock:
    @pytest.mark.parametrize("rel", [
        "docs/gates/orient_decision.md",
        "docs/gates/interview_decision.md",
        "docs/gates/model_decision.md",
        "docs/gates/seed_decision.md",
        "docs/plan/model_skip_waiver.md",
        "docs/literature/literature_skip_waiver.md",
    ])
    def test_blocks_agent_write_to_decision_file(self, project, rel):
        rc, err = run_pre_write(project, project / rel)
        assert rc == 2
        assert "HUMAN-OWNED GATE FILE" in err

    def test_allows_agent_write_to_proposal_note(self, project):
        # The lab may freely draft its proposal in the gate note.
        rc, err = run_pre_write(project, project / "docs" / "gates" / "orient_note.md")
        assert rc == 0


# ── Gate checkers require the PI decision (and honour --project) ──────────────

class TestGateNeedsDecision:
    def test_orient_gate_closed_until_decision(self, project):
        (project / "docs" / "gates" / "orient_note.md").write_text(
            "## Task Classification\n- New model\n\n"
            "## Responsible Role\n- Lead Agent\n\n"
            "## First Professor Question\nWhat regime?\n"
        )
        rc, _, _ = run_checker("check_orient_recorded.py", project)
        assert rc == 1  # note recorded, decision missing → gate closed

        (project / "docs" / "gates" / "orient_decision.md").write_text(
            "## Decision\nApproved — proceed to interview.\n"
        )
        rc, _, _ = run_checker("check_orient_recorded.py", project)
        assert rc == 0  # PI decision present → gate open

    def test_blank_decision_does_not_open_gate(self, project):
        (project / "docs" / "gates" / "orient_note.md").write_text(
            "## Task Classification\n- x\n\n## Responsible Role\n- Lead\n\n"
            "## First Professor Question\nQ?\n"
        )
        # Only a comment under ## Decision → still blank → still closed.
        (project / "docs" / "gates" / "orient_decision.md").write_text(
            "## Decision\n<!-- approve / revise / reject -->\n"
        )
        rc, _, _ = run_checker("check_orient_recorded.py", project)
        assert rc == 1


# ── The seed gate sign-off is never waived by the bypass ─────────────────────

class TestSeedDecisionUnbypassable:
    def _heavy_run(self, project: Path, env: dict) -> tuple[int, str]:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_seed_before_full_run.py")],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "python src/run_experiment.py"},
            }),
            capture_output=True, text=True, cwd=str(project), env=env,
        )
        return proc.returncode, proc.stderr.strip()

    def test_bypass_waives_smoke_but_not_pi_decision(self, project):
        # Smoke run not even recorded, but bypass is set → smoke requirement waived…
        env = dict(os.environ)
        env["RESEARCH_HARNESS_BYPASS_SEED_GATE"] = "1"
        rc, err = self._heavy_run(project, env)
        assert rc == 2  # …yet the PI's seed_decision is still required
        assert "seed_decision" in err

        # PI records the decision → heavy run allowed even on the bypass path.
        (project / "docs" / "gates" / "seed_decision.md").write_text(
            "## Decision\nApprove full-scale runs.\n"
        )
        rc, _ = self._heavy_run(project, env)
        assert rc == 0
