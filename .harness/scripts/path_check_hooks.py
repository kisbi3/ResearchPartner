#!/usr/bin/env python3
"""Path-aware hook dispatcher for Write/Edit/Bash/PowerShell tool calls.

The Claude Code hook system matches by tool name (matcher: "Write|Edit"),
not by file path, so any path-specific check needs an in-script dispatcher.
This module reads the hook JSON from stdin and runs the right check(s)
based on the file_path involved.

Usage (set in .claude/settings.local.json):
    python .harness/scripts/path_check_hooks.py pre
    python .harness/scripts/path_check_hooks.py post

Registered checks:

  PRE (BLOCKING — exit 2 fails the tool call):
    docs/gates/*_decision.md          → human-owned (every agent write blocked)
    literature/reviews/*.md           → check_paper_review_quality
    AGENTS.md / GEMINI.md             → check_contract_sync
    docs/claims/*.md                  → check_claim_promotion_freshness

  POST (WARN-ONLY — always exit 0):
    outputs/figures/*.{png,pdf,svg,jpg,jpeg}  → check_figure_provenance

Notes:
- For Bash/PowerShell post events we don't get a file_path in tool_input,
  so the figure-provenance check fires on every Bash post; it's cheap and
  warn-only.
- check_paper_review_quality reads the file path from the Write tool input
  directly, so it sees the new content even before the file is committed
  to disk (Pre-hook fires after the tool call payload is assembled but
  before it executes — see Claude Code hook docs).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
import _project_root as project_root_mod  # noqa: E402


def _load_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _matches_literature_review(rel: str) -> bool:
    # literature/reviews/<paper_id>.md
    return rel.startswith("literature/reviews/") and rel.endswith(".md")


def _matches_contract(rel: str) -> bool:
    return rel in ("AGENTS.md", "GEMINI.md")


def _matches_claim(rel: str) -> bool:
    return rel.startswith("docs/claims/") and rel.endswith(".md")


# The brake: researcher-owned gate-decision files. The lab (every agent,
# including the Lead) drafts proposals in the matching *_note/_spec files, but
# the *decision* is the PI's to write — so the lab cannot forge its own approval
# or its own bypass. Enforced as a hard write-block (exit 2) on any agent
# Write/Edit.
_HUMAN_OWNED_DECISIONS = frozenset({
    "docs/gates/orient_decision.md",
    "docs/gates/interview_decision.md",
    "docs/gates/model_decision.md",
    "docs/gates/seed_decision.md",
    "docs/gates/adoption_decision.md",
    "docs/plan/model_skip_waiver.md",
    "docs/literature/literature_skip_waiver.md",
})


def _matches_human_owned(rel: str) -> bool:
    return rel in _HUMAN_OWNED_DECISIONS


def _matches_figure(rel: str) -> bool:
    if not rel.startswith("outputs/figures/"):
        return False
    return rel.lower().endswith((".png", ".pdf", ".svg", ".jpg", ".jpeg"))


# ── PRE hooks ────────────────────────────────────────────────────────────────

def _check_paper_review_pre(file_path: Path, project: Path) -> tuple[int, list[str]]:
    """Block writes of empty / placeholder paper reviews."""
    if not file_path.exists():
        # File doesn't exist yet — the agent is creating it. We can't check
        # quality of content we haven't seen; defer to PostToolUse. (We could
        # parse `tool_input["content"]` but that's only available in the new-
        # file Write case, not Edit; skip to keep the dispatcher uniform.)
        return 0, []
    try:
        from check_paper_review_quality import check_review_quality  # noqa: PLC0415
        result = check_review_quality(file_path)
    except Exception as exc:
        return 0, [f"check_paper_review_quality dispatcher error: {exc}"]
    if result.status == "pass":
        return 0, []
    missing = ", ".join(result.missing[:5]) + ("…" if len(result.missing) > 5 else "")
    return 2, [
        f"Paper review {file_path.name} is incomplete — missing: {missing}.\n"
        "Fill in the required sections / links / caveats before saving."
    ]


def _check_claim_freshness_pre(
    file_path: Path,
    tool_name: str,
    tool_input: dict,
    project: Path,
) -> tuple[int, list[str]]:
    """Block promoted claim writes whose cited outputs are stale (>24h).

    Reconstructs the post-edit content from tool_input so the check runs
    against what is about to be written, not the on-disk version.
    """
    try:
        from check_claim_promotion_freshness import check_claim_freshness  # noqa: PLC0415
    except Exception as exc:
        return 0, [f"check_claim_promotion_freshness import error: {exc}"]

    content = ""
    if tool_name == "Write":
        content = tool_input.get("content", "") or ""
    elif tool_name == "Edit":
        # Best-effort: merge current file with the new_string. We can't fully
        # simulate Edit's replace semantics without doing the actual edit, so
        # we union: read current file (if present) + new_string. False
        # negatives are acceptable (gate is conservative); false positives
        # would only fire if the promoted+output keywords appear in
        # new_string itself.
        current = ""
        try:
            current = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
        new_str = tool_input.get("new_string", "") or ""
        content = current + "\n" + new_str

    if not content:
        return 0, []

    result = check_claim_freshness(file_path, content, project)
    if result.status != "fail":
        return 0, []
    bits = []
    if result.stale:
        bits.append("stale: " + ", ".join(result.stale[:3]))
    if result.missing:
        bits.append("missing: " + ", ".join(result.missing[:3]))
    if result.adopted_unvalidated:
        bits.append("adopted-unvalidated: " + ", ".join(result.adopted_unvalidated[:3]))
    detail = "; ".join(bits) if bits else result.reason
    return 2, [
        f"PROMOTED CLAIM BLOCKED — freshness/finding lifecycle check failed ({detail}).\n"
        "  Rule: a promoted claim (ceiling > observation) must cite outputs/\n"
        "        artifacts modified within the last 24 hours. Mechanism and\n"
        "        generalization claims must also have a resolved Finding Lifecycle\n"
        "        with Evidence Paths Read Directly. In adoption mode, it may not\n"
        "        lean on an adopted artifact still marked partial/unknown/failed/\n"
        "        deprecated in the adoption inventory.\n"
        "  Fix:  re-run stale figure/data generators or update the claim file with\n"
        "        independently_checked + evidence_linked finding state and direct\n"
        "        evidence paths; reproduce + validate any adopted artifact (record\n"
        "        it in baseline_registry.md). If the evidence is weaker, lower the\n"
        "        ceiling."
    ]


def _check_contract_sync_pre() -> tuple[int, list[str]]:
    """Block AGENTS.md / GEMINI.md drift."""
    try:
        import check_contract_sync as ccs  # noqa: PLC0415
        # The script reads ROOT-relative pairs; we just invoke its main with []
        rc = ccs.main([])
        return (0, []) if rc == 0 else (2, [
            "AGENTS.md and GEMINI.md must be byte-identical. Re-sync the two "
            "before continuing."
        ])
    except Exception as exc:
        return 0, [f"check_contract_sync dispatcher error: {exc}"]


def _check_human_owned_pre(rel: str) -> tuple[int, list[str]]:
    """Hard-block any agent write to a researcher-owned gate-decision file.

    This is the brake. The lab proposes; only the researcher (PI) records the
    decision. Because the agent cannot write these files, a gate that requires
    one cannot be satisfied by the agent rubber-stamping its own results.
    """
    return 2, [
        f"HUMAN-OWNED GATE FILE — {rel} records the researcher's (PI) decision "
        "and cannot be written by an agent.\n"
        "  The lab may draft its proposal in the matching gate note (e.g. "
        "docs/gates/orient_note.md), but the decision is the researcher's to write.\n"
        "  STOP: present the proposal to the researcher and ask them to record "
        "their decision directly in this file. The gate stays closed until they do."
    ]


# ── POST hooks ───────────────────────────────────────────────────────────────

def _check_figure_provenance_post(project: Path) -> tuple[int, list[str]]:
    """Warn (never block) if any figure under outputs/figures/ lacks provenance."""
    try:
        from check_figure_provenance import check  # noqa: PLC0415
        missing = check(project / "outputs" / "figures")
    except Exception as exc:
        return 0, [f"check_figure_provenance dispatcher error: {exc}"]
    if not missing:
        return 0, []
    head = ", ".join(missing[:3]) + ("…" if len(missing) > 3 else "")
    return 0, [
        f"PROVENANCE WARNING: {len(missing)} figure(s) lack a provenance record "
        f"(e.g. {head}). Add <stem>.provenance.md or update "
        "outputs/figures/figure_provenance.md."
    ]


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("pre", "post"):
        return 0
    phase = sys.argv[1]

    payload = _load_payload()
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    file_path_str = tool_input.get("file_path", "")

    # Resolve project root from cwd (the file may not exist yet on PRE).
    try:
        project = project_root_mod.resolve_project(None, require=True)
    except project_root_mod.ProjectRootNotFoundError:
        return 0  # Not inside a research project — no path-based checks apply.

    rel = ""
    if file_path_str:
        try:
            rel = Path(file_path_str).resolve().relative_to(project).as_posix()
        except (ValueError, OSError):
            rel = ""

    blocking_failures: list[str] = []
    warnings: list[str] = []

    if phase == "pre" and tool_name in ("Write", "Edit") and rel:
        if _matches_human_owned(rel):
            code, msgs = _check_human_owned_pre(rel)
            (blocking_failures if code != 0 else warnings).extend(msgs)
        if _matches_literature_review(rel):
            code, msgs = _check_paper_review_pre(Path(file_path_str), project)
            (blocking_failures if code != 0 else warnings).extend(msgs)
        if _matches_contract(rel):
            code, msgs = _check_contract_sync_pre()
            (blocking_failures if code != 0 else warnings).extend(msgs)
        if _matches_claim(rel):
            code, msgs = _check_claim_freshness_pre(
                Path(file_path_str), tool_name, tool_input, project
            )
            (blocking_failures if code != 0 else warnings).extend(msgs)

    if phase == "post":
        # Figure provenance — fire on Write/Edit of a figure, OR on any Bash/PowerShell
        # post (since shell-created files don't have a file_path).
        if tool_name in ("Bash", "PowerShell") or _matches_figure(rel):
            _, msgs = _check_figure_provenance_post(project)
            warnings.extend(msgs)

    for w in warnings:
        print(w, file=sys.stderr)

    if blocking_failures:
        for f in blocking_failures:
            print(f, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
