#!/usr/bin/env python3
"""Path-aware hook dispatcher for Write/Edit/Bash/PowerShell tool calls.

The Claude Code hook system matches by tool name (matcher: "Write|Edit"),
not by file path, so any path-specific check needs an in-script dispatcher.
This module reads the hook JSON from stdin and runs the right check(s)
based on the file_path involved.

Usage (set in .claude/settings.local.json):
    python scripts/path_check_hooks.py pre
    python scripts/path_check_hooks.py post

Registered checks:

  PRE (BLOCKING — exit 2 fails the tool call):
    literature/reviews/*.md           → check_paper_review_quality
    AGENTS.md / GEMINI.md             → check_contract_sync

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
        if _matches_literature_review(rel):
            code, msgs = _check_paper_review_pre(Path(file_path_str), project)
            (blocking_failures if code != 0 else warnings).extend(msgs)
        if _matches_contract(rel):
            code, msgs = _check_contract_sync_pre()
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
