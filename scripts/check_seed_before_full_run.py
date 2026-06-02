#!/usr/bin/env python3
"""Bash PRE hook: require seed/stage-1 pass before a full-scale run.

The pattern this gate prevents:

    1. AI writes an experiment script under src/.
    2. AI invokes ``python src/run_full_experiment.py`` directly.
    3. Hours of compute later, a bug or misconfiguration surfaces that a
       seed-stage smoke-run would have caught in seconds.

When the Bash/PowerShell command looks like a heavy run (a Python invocation
of a script whose name matches RUN_PATTERNS), this hook requires BOTH a
Status=pass entry in ``docs/gates/seed_design.md`` (the smoke run) AND a
non-empty ``## Decision`` in ``docs/gates/seed_decision.md`` (the PI's
sign-off, write-blocked for agents). If either is absent, the call is blocked.

Detection is intentionally conservative: only block obvious heavy-run names
to avoid false positives on utility scripts (e.g. ``python scripts/foo.py``,
test commands, lint, etc.).

Heavy-run name patterns (case-insensitive, substring on script stem):
    run, train, fit, experiment, simulate, scan, sweep,
    full, production, deploy

Bypass: set ``RESEARCH_HARNESS_BYPASS_SEED_GATE=1`` for an explicit one-off
waiver of the smoke-run requirement only (logged to stderr). The PI's
seed_decision is the brake and is NEVER waived.

Exit codes:
    0 — allow (not a heavy run; or smoke pass + PI seed_decision; or bypass set
        with the PI seed_decision present)
    2 — block (heavy run without the smoke pass, or without the PI's seed_decision)
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import _project_root as project_root_mod  # noqa: E402

# Stem keywords that mark a script as a heavy run. Substring match,
# case-insensitive.
RUN_PATTERNS = (
    "run", "train", "fit", "experiment", "experiment_",
    "simulate", "simulation", "scan", "sweep",
    "full", "production", "deploy",
)

# Stems that look heavy but should be allowed (utility scripts that happen
# to contain a heavy keyword).
ALLOWLIST_STEMS = {
    "run_with_checkpoint",  # harness wrapper
    "run_tests",
    "scan_files",
}

# Directories that exempt scripts (utility/tooling lives here).
EXEMPT_DIRS = ("scripts/", "tools/", "tests/", "test/")


def _extract_python_targets(command: str) -> list[str]:
    """Return the script paths a Bash command line invokes via python.

    Handles forms like:
        python src/run.py --arg
        python3 -u src/foo.py
        py -3 src/bar.py
        python -m my_module.run
        & python src/run.py   (PowerShell call operator)
    """
    targets: list[str] = []
    # Split on shell separators that start a new command.
    chunks = re.split(r"(?:&&|\|\||;|\||\n)", command)
    for chunk in chunks:
        try:
            tokens = shlex.split(chunk, posix=False)
        except ValueError:
            tokens = chunk.split()
        if not tokens:
            continue
        # Skip leading PowerShell call-operator / env-prefix tokens.
        while tokens and tokens[0] in ("&", "exec"):
            tokens.pop(0)
        if not tokens:
            continue
        head = Path(tokens[0]).name.lower().rstrip(".exe")
        if head not in {"python", "python3", "py", "python.exe", "python3.exe"}:
            continue
        # Skip "py -3" or "python -u" style flags to find the script arg.
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok == "-m" and i + 1 < len(tokens):
                targets.append(tokens[i + 1])
                break
            if tok.startswith("-"):
                i += 1
                continue
            targets.append(tok.strip('"').strip("'"))
            break
    return targets


def _looks_heavy(target: str) -> bool:
    norm = target.replace("\\", "/").lower()
    if any(norm.startswith(d) or f"/{d}" in norm for d in EXEMPT_DIRS):
        return False
    stem = Path(norm).stem
    if stem in ALLOWLIST_STEMS:
        return False
    return any(kw in stem for kw in RUN_PATTERNS)


def _seed_gate_passed(project: Path) -> bool:
    """Return True iff docs/gates/seed_design.md has a Status=pass row."""
    seed = project / "docs" / "gates" / "seed_design.md"
    if not seed.is_file():
        return False
    text = seed.read_text(encoding="utf-8", errors="replace")
    # Look for any line containing "pass" in a markdown table cell.
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if "pass" in cells:
            return True
    # Fallback: a heading like "## Seed run: PASS"
    if re.search(r"(?im)^\s*#{1,6}.*\bseed\b.*\bpass\b", text):
        return True
    return False


def _seed_decision_recorded(project: Path) -> bool:
    """Return True iff docs/gates/seed_decision.md has a non-empty '## Decision'.

    This is the researcher (PI) sign-off to proceed from a passing smoke run to
    full-scale compute. Agents are hook-blocked from writing this file, so the
    lab cannot approve its own production runs.
    """
    decision = project / "docs" / "gates" / "seed_decision.md"
    if not decision.is_file():
        return False
    text = decision.read_text(encoding="utf-8", errors="replace")
    in_section = False
    for line in text.splitlines():
        if line.strip() == "## Decision":
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                return True
    return False


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Bash", "PowerShell"):
        return 0

    command = (payload.get("tool_input", {}) or {}).get("command", "") or ""
    if not command:
        return 0

    targets = _extract_python_targets(command)
    heavy = [t for t in targets if _looks_heavy(t)]
    if not heavy:
        return 0

    try:
        project = project_root_mod.resolve_project(None, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return 0

    target_list = ", ".join(heavy)
    bypass = os.environ.get("RESEARCH_HARNESS_BYPASS_SEED_GATE") == "1"

    if not bypass and not _seed_gate_passed(project):
        print(
            f"SEED GATE BLOCK: heavy run detected ({target_list}) but no "
            f"Status=pass row in docs/gates/seed_design.md.\n"
            f"\n"
            f"  Rule: a full-scale Python run must be preceded by a seed/stage-1\n"
            f"        pass — otherwise hours of compute can be wasted on a bug\n"
            f"        that a smoke run would have caught.\n"
            f"\n"
            f"  Fix:  (1) run the same script with a tiny config (n=10, 1 epoch,\n"
            f"            etc.); (2) record the result as a Status=pass row in\n"
            f"            docs/gates/seed_design.md; (3) retry the full run.\n"
            f"\n"
            f"  Bypass: set RESEARCH_HARNESS_BYPASS_SEED_GATE=1 for an explicit\n"
            f"          one-off waiver (logged to stderr).",
            file=sys.stderr,
        )
        return 2

    if not _seed_decision_recorded(project):
        print(
            f"SEED GATE BLOCK: heavy run detected ({target_list}). The seed/stage-1\n"
            f"smoke run passed, but the researcher has not approved full-scale runs.\n"
            f"\n"
            f"  Rule: the jump from a smoke run to production compute also needs the\n"
            f"        PI's sign-off. The lab cannot approve its own full-scale runs.\n"
            f"\n"
            f"  Fix:  ask the researcher to record 'approve' in the '## Decision'\n"
            f"        section of docs/gates/seed_decision.md. Agents cannot write\n"
            f"        that file (it is hook-blocked).\n"
            f"\n"
            f"  No bypass: the PI's seed_decision is the brake — the bypass env\n"
            f"          var waives only the smoke-run requirement, not this sign-off.",
            file=sys.stderr,
        )
        return 2

    if bypass:
        print(
            "SEED-GATE BYPASS: smoke-run requirement waived via "
            "RESEARCH_HARNESS_BYPASS_SEED_GATE=1; the PI's seed_decision is still "
            "required (and is present).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
