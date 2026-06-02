"""Regression coverage for the harness's enforcement hooks.

Covers (as subprocess invocations that simulate Claude Code's hook contract):
- scripts/check_src_write_authorization.py (Write|Edit code-write gate)
- scripts/check_bash_code_write.py (Bash|PowerShell code-write gate)
- scripts/check_cross_tier_compliance.py (stage-gate backstop)
- scripts/check_claim_promotion.py (claim ceiling gate w/ diversity)
- scripts/check_peer_review_invocation.py (meeting context gate)
- scripts/check_spawn_log_integrity.py (forged-row detector)

Each hook is invoked as a child Python process so the test exercises the
exact stdin/stdout/exit-code contract Claude Code uses at runtime.
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


def run_hook(script: str, payload: dict | None = None, *, env: dict | None = None,
             args: list[str] | None = None) -> tuple[int, str, str]:
    """Invoke a hook script with JSON payload on stdin; return (rc, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPTS / script)]
    if args:
        cmd.extend(args)
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload) if payload is not None else "",
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


@pytest.fixture
def run_dir(tmp_path):
    # v3 layout: the project root IS the research root, marked by .research-harness.
    run = tmp_path / "proj"
    (run / "src").mkdir(parents=True)
    (run / "docs" / "gates").mkdir(parents=True)
    (run / ".research-harness").write_text("")
    return run


def write_spawn_log(run_dir: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    """Write spawn log with given (date, role, file, task, status) rows."""
    lines = ["| Date | Role | File | Task | Status |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    (run_dir / "docs" / "gates" / "agent_spawn_log.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_validation_log(run_dir: Path, rows: list[tuple[str, str, str, str, str]]) -> None:
    """Write validation log with given (date, check, target, status, evidence) rows."""
    lines = ["| Date | Check | Target | Status | Evidence |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    (run_dir / "docs" / "gates" / "validation_log.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_valid_claim_lifecycle(run_dir: Path, ceiling: str) -> None:
    """Write a claim file satisfying mechanism/generalization lifecycle checks."""
    evidence = run_dir / "outputs" / "data" / "direct_read.csv"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("evidence\n", encoding="utf-8")
    claims = run_dir / "docs" / "claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / f"claim_{ceiling}.md").write_text(
        f"""\
ceiling: {ceiling}

## Claim

outputs/data/direct_read.csv supports this {ceiling} claim.

## Finding Lifecycle

### Finding

Status: independently_checked
Claim affected: claim_{ceiling}
Evidence paths:
- outputs/data/direct_read.csv

### Independent Check

Checker: scientific-validator
Result: independently_checked

### Evidence Link

Status: evidence_linked

### Evidence Paths Read Directly

- outputs/data/direct_read.csv
""",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# check_src_write_authorization.py
# ---------------------------------------------------------------------------

class TestSrcWriteAuthorization:
    SCRIPT = "check_src_write_authorization.py"

    def test_allows_non_run_path(self, tmp_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(tmp_path / "foo.py")},
        })
        assert rc == 0

    def test_blocks_run_src_without_spawn_log(self, run_dir):
        target = run_dir / "src" / "sim.py"
        rc, _, err = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 2
        assert "CROSS-TIER BLOCK" in err

    def test_allows_with_matching_spawn_log_entry(self, run_dir):
        target = run_dir / "src" / "sim.py"
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
        ])
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 0

    def test_blocks_tests_dir_writes(self, run_dir):
        (run_dir / "tests").mkdir()
        target = run_dir / "tests" / "test_sim.py"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 2

    def test_blocks_ipynb(self, run_dir):
        (run_dir / "notebooks").mkdir()
        target = run_dir / "notebooks" / "explore.ipynb"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 2

    def test_exempts_docs_dir(self, run_dir):
        (run_dir / "docs").mkdir(exist_ok=True)
        target = run_dir / "docs" / "note.py"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 0

    def test_exempts_literature_dir(self, run_dir):
        (run_dir / "literature").mkdir()
        target = run_dir / "literature" / "extract.py"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 0

    def test_ignores_non_code_extension(self, run_dir):
        target = run_dir / "src" / "data.json"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        })
        assert rc == 0

    def test_bypass_env_var(self, run_dir):
        env = dict(os.environ)
        env["RESEARCH_HARNESS_BYPASS_SRC_GATE"] = "1"
        target = run_dir / "src" / "sim.py"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Write",
            "tool_input": {"file_path": str(target)},
        }, env=env)
        assert rc == 0


# ---------------------------------------------------------------------------
# check_bash_code_write.py
# ---------------------------------------------------------------------------

class TestBashCodeWrite:
    SCRIPT = "check_bash_code_write.py"

    @pytest.fixture
    def covered_path(self, tmp_path):
        run = tmp_path / "proj"
        (run / "src").mkdir(parents=True)
        (run / ".research-harness").write_text("")
        return (run / "src" / "sim.py").as_posix()

    def test_ignores_non_bash_tools(self):
        rc, _, _ = run_hook(self.SCRIPT, {"tool_name": "Write", "tool_input": {}})
        assert rc == 0

    def test_allows_read_only_bash(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"python {covered_path}"},
        })
        assert rc == 0

    def test_blocks_redirect_to_run_src(self, covered_path):
        rc, _, err = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo 'print(1)' > {covered_path}"},
        })
        assert rc == 2
        assert "CROSS-TIER BLOCK" in err

    def test_blocks_append_redirect(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo extra >> {covered_path}"},
        })
        assert rc == 2

    def test_blocks_sed_in_place(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"sed -i 's/foo/bar/' {covered_path}"},
        })
        assert rc == 2

    def test_blocks_cp_to_covered(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"cp /tmp/other.py {covered_path}"},
        })
        assert rc == 2

    def test_blocks_python_dash_c_open(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"python -c \"open('{covered_path}', 'w').write('x')\""
            },
        })
        assert rc == 2

    def test_blocks_powershell_set_content(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "PowerShell",
            "tool_input": {"command": f"Set-Content -Path {covered_path} -Value 'x'"},
        })
        assert rc == 2

    def test_blocks_heredoc_redirect(self, covered_path):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"cat <<EOF > {covered_path}\nprint(1)\nEOF"},
        })
        assert rc == 2

    def test_exempts_docs_path(self, tmp_path):
        run = tmp_path / "proj"
        (run / "docs").mkdir(parents=True)
        (run / ".research-harness").write_text("")
        target = (run / "docs" / "note.py").as_posix()
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo x > {target}"},
        })
        assert rc == 0

    def test_ignores_non_run_redirect(self, tmp_path):
        target = (tmp_path / "outside.py").as_posix()
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo x > {target}"},
        })
        assert rc == 0

    def test_bypass_env_var(self, covered_path):
        env = dict(os.environ)
        env["RESEARCH_HARNESS_BYPASS_SRC_GATE"] = "1"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo x > {covered_path}"},
        }, env=env)
        assert rc == 0


# ---------------------------------------------------------------------------
# check_cross_tier_compliance.py
# ---------------------------------------------------------------------------

class TestCrossTierCompliance:
    SCRIPT = "check_cross_tier_compliance.py"

    def test_passes_when_src_matches_spawns(self, run_dir):
        (run_dir / "src" / "sim.py").write_text("")
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
        ])
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 0

    def test_warns_when_src_exceeds_spawns(self, run_dir):
        (run_dir / "src" / "sim.py").write_text("")
        (run_dir / "src" / "plot.py").write_text("")
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
        ])
        rc, _, err = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 2
        assert "CROSS-TIER FAIL" in err

    def test_unknown_passes_without_strict(self, run_dir):
        (run_dir / "src" / "sim.py").write_text("")
        # No spawn log file
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 0

    def test_unknown_fails_with_strict(self, run_dir):
        (run_dir / "src" / "sim.py").write_text("")
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--strict"])
        assert rc == 2


# ---------------------------------------------------------------------------
# check_claim_promotion.py
# ---------------------------------------------------------------------------

class TestClaimPromotion:
    SCRIPT = "check_claim_promotion.py"

    def test_observation_always_allowed(self, run_dir):
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "observation"])
        assert rc == 0

    def test_interpretation_blocks_with_zero_passes(self, run_dir):
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "interpretation"])
        assert rc == 2

    def test_interpretation_allows_with_one_pass(self, run_dir):
        write_validation_log(run_dir, [
            ("2026-05-17", "convergence", "t1", "pass", "a"),
        ])
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "interpretation"])
        assert rc == 0

    def test_mechanism_blocks_without_baseline_class(self, run_dir):
        # Two passes but none are baseline-class
        write_validation_log(run_dir, [
            ("2026-05-17", "convergence", "t1", "pass", "a"),
            ("2026-05-17", "smoke",       "t2", "pass", "b"),
        ])
        rc, _, err = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "mechanism"])
        assert rc == 2
        assert "baseline-class" in err

    def test_mechanism_allows_with_baseline_class(self, run_dir):
        write_validation_log(run_dir, [
            ("2026-05-17", "convergence", "t1", "pass", "a"),
            ("2026-05-17", "toy_model",   "t2", "pass", "b"),
        ])
        write_valid_claim_lifecycle(run_dir, "mechanism")
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "mechanism"])
        assert rc == 0

    def test_generalization_blocks_with_single_category(self, run_dir):
        write_validation_log(run_dir, [
            ("2026-05-17", "toy_model", "t1", "pass", "a"),
            ("2026-05-17", "toy_model", "t2", "pass", "b"),
            ("2026-05-17", "toy_model", "t3", "pass", "c"),
        ])
        rc, _, err = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "generalization"])
        assert rc == 2
        assert "distinct check categories" in err

    def test_generalization_allows_with_diversity(self, run_dir):
        write_validation_log(run_dir, [
            ("2026-05-17", "toy_model",    "t1", "pass", "a"),
            ("2026-05-17", "reproduction", "t2", "pass", "b"),
            ("2026-05-17", "conservation", "t3", "pass", "c"),
        ])
        write_valid_claim_lifecycle(run_dir, "generalization")
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir), "--target", "generalization"])
        assert rc == 0


# ---------------------------------------------------------------------------
# check_peer_review_invocation.py
# ---------------------------------------------------------------------------

class TestPeerReviewInvocation:
    SCRIPT = "check_peer_review_invocation.py"

    def test_ignores_non_agent_tool(self):
        rc, _, _ = run_hook(self.SCRIPT, {"tool_name": "Write", "tool_input": {}})
        assert rc == 0

    def test_allows_non_peer_review_spawn(self):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Agent",
            "tool_input": {
                "prompt": "You are a Graduate Student. Load skills/graduate-student/SKILL.md"
            },
        })
        assert rc == 0

    def test_blocks_peer_review_without_meeting(self):
        rc, _, err = run_hook(self.SCRIPT, {
            "tool_name": "Agent",
            "tool_input": {
                "prompt": "You are a Peer-Review Professor. Load skills/peer-review-professor/SKILL.md"
            },
        })
        assert rc == 2
        assert "PEER-REVIEW BLOCK" in err

    def test_allows_when_prompt_references_meeting_scope_review(self):
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Agent",
            "tool_input": {
                "prompt": (
                    "meeting --scope review --on 'is the claim X?'. "
                    "You are a Peer-Review Professor. Load skills/peer-review-professor/SKILL.md"
                )
            },
        })
        assert rc == 0

    def test_bypass_env_var(self):
        env = dict(os.environ)
        env["RESEARCH_HARNESS_BYPASS_MEETING_GATE"] = "1"
        rc, _, _ = run_hook(self.SCRIPT, {
            "tool_name": "Agent",
            "tool_input": {
                "prompt": "Load skills/peer-review-professor/SKILL.md"
            },
        }, env=env)
        assert rc == 0


# ---------------------------------------------------------------------------
# check_spawn_log_integrity.py
# ---------------------------------------------------------------------------

class TestSpawnLogIntegrity:
    SCRIPT = "check_spawn_log_integrity.py"

    def test_no_spawn_log_passes(self, run_dir):
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 0

    def test_warns_when_diagram_missing(self, run_dir):
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
        ])
        # No diagram file — script should warn but not fail
        rc, _, err = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 0
        assert "INTEGRITY WARN" in err

    def test_passes_when_diagram_has_matching_events(self, run_dir):
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
        ])
        diagram = run_dir / "docs" / "live_workflow_diagram.md"
        diagram.parent.mkdir(parents=True, exist_ok=True)
        diagram.write_text(
            "# Live\n\n## Real-Time Event Log\n\n"
            "🔄 `2026-05-17 12:34 UTC` | `start` | **You are a Graduate Student** | _lead-agent_\n"
        )
        rc, _, _ = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 0

    def test_fails_when_spawn_rows_exceed_events(self, run_dir):
        write_spawn_log(run_dir, [
            ("2026-05-17", "graduate-student", "src/sim.py", "T1", "complete"),
            ("2026-05-17", "graduate-student", "src/plot.py", "T2", "complete"),
            ("2026-05-17", "graduate-student", "src/fake.py", "TX", "complete"),
        ])
        diagram = run_dir / "docs" / "live_workflow_diagram.md"
        diagram.parent.mkdir(parents=True, exist_ok=True)
        diagram.write_text(
            "# Live\n\n## Real-Time Event Log\n\n"
            "🔄 `2026-05-17 12:34 UTC` | `start` | **You are a Graduate Student for T1** | _lead-agent_\n"
        )
        rc, _, err = run_hook(self.SCRIPT, args=["--run", str(run_dir)])
        assert rc == 2
        assert "INTEGRITY FAIL" in err
