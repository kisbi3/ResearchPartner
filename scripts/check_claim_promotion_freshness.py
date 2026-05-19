#!/usr/bin/env python3
"""Claim promotion freshness gate.

When a claim file under ``docs/claims/`` is written/edited with a non-
``observation`` ceiling (or ``status: promoted``), every output artifact it
cites (``outputs/figures/...``, ``outputs/data/...``, ``outputs/tables/...``)
must exist on disk and have been modified within the freshness window
(default 24 h).

Why
---
The most common stale-evidence failure pattern is:

    1. Researcher generates figure F at t0.
    2. Code/model evolves over the next several days.
    3. AI promotes a claim citing F at t0+5d without re-running.

The claim then misrepresents *current* behaviour as having been validated.
This gate blocks the promotion until the cited figures are refreshed.

Public API (used by ``path_check_hooks.py``)::

    from check_claim_promotion_freshness import check_claim_freshness
    result = check_claim_freshness(file_path, content, project, window_hours=24)
    # result.status in {"pass", "skip", "fail"}; result.stale is list[str].

Exit codes (CLI)::
    0 — pass / skip (no promoted claim, or all citations fresh)
    1 — fail (one or more stale / missing references)
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import _project_root as project_root_mod  # noqa: E402

# ── Detection patterns ───────────────────────────────────────────────────────
# A claim is considered "promoted" if it carries any non-observation ceiling.
PROMOTED_CEILING_RE = re.compile(
    r"(?im)^\s*(?:ceiling|claim[-_\s]?ceiling|status)\s*:\s*"
    r"(interpretation|mechanism|generalization|promoted)\b"
)

# References to output artifacts. Accepts ./outputs/... or outputs/... with
# either forward or back slashes.
OUTPUT_REF_RE = re.compile(
    r"(?:\./)?outputs[\\/](?:figures|data|tables)[\\/][\w\-./\\]+"
)


@dataclass
class FreshnessResult:
    status: str  # "pass" | "skip" | "fail"
    stale: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    fresh: list[str] = field(default_factory=list)
    reason: str = ""


def _is_promoted(text: str) -> bool:
    return bool(PROMOTED_CEILING_RE.search(text))


def _find_output_refs(text: str) -> list[str]:
    # De-dupe while preserving order; normalise separators.
    seen: dict[str, None] = {}
    for match in OUTPUT_REF_RE.findall(text):
        norm = match.replace("\\", "/").lstrip("./")
        seen.setdefault(norm, None)
    return list(seen.keys())


def check_claim_freshness(
    file_path: Path,
    content: str,
    project: Path,
    window_hours: int = 24,
) -> FreshnessResult:
    """Return a FreshnessResult for *content* (intended write/edit body)."""
    if not _is_promoted(content):
        return FreshnessResult(status="skip", reason="not a promoted claim")

    refs = _find_output_refs(content)
    if not refs:
        return FreshnessResult(
            status="fail",
            reason=(
                "promoted claim cites no outputs/ artifact — every promoted "
                "claim must reference at least one figure/data/table under "
                "outputs/."
            ),
        )

    window_seconds = window_hours * 3600
    now = time.time()
    stale: list[str] = []
    missing: list[str] = []
    fresh: list[str] = []

    for ref in refs:
        target = (project / ref).resolve()
        if not target.exists():
            missing.append(ref)
            continue
        age = now - target.stat().st_mtime
        if age > window_seconds:
            hours_old = int(age // 3600)
            stale.append(f"{ref} ({hours_old}h old)")
        else:
            fresh.append(ref)

    if stale or missing:
        return FreshnessResult(
            status="fail",
            stale=stale,
            missing=missing,
            fresh=fresh,
            reason=(
                f"{len(stale)} stale + {len(missing)} missing reference(s) "
                f"in a promoted claim (window={window_hours}h)"
            ),
        )
    return FreshnessResult(
        status="pass",
        fresh=fresh,
        reason=f"all {len(fresh)} reference(s) fresh (window={window_hours}h)",
    )


def check_project(
    project: Path,
    window_hours: int = 24,
) -> tuple[int, list[str]]:
    """Scan all promoted claims in docs/claims/ for freshness.

    Used as a CLI / standalone audit. Returns (0, [...]) when every promoted
    claim is fresh, (1, [...]) otherwise.
    """
    claims_dir = project / "docs" / "claims"
    if not claims_dir.is_dir():
        return 0, ["No docs/claims/ directory — nothing to audit."]

    failures: list[str] = []
    audited = 0
    for path in sorted(claims_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        result = check_claim_freshness(path, text, project, window_hours)
        if result.status == "skip":
            continue
        audited += 1
        if result.status == "fail":
            detail = []
            if result.stale:
                detail.append("stale=" + ", ".join(result.stale[:3]))
            if result.missing:
                detail.append("missing=" + ", ".join(result.missing[:3]))
            failures.append(
                f"{path.relative_to(project).as_posix()}: {result.reason}"
                + (f" [{'; '.join(detail)}]" if detail else "")
            )
    if failures:
        return 1, failures
    return 0, [f"Audited {audited} promoted claim(s); all citations fresh."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--window-hours", type=int, default=24)
    args = parser.parse_args(argv)

    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    code, messages = check_project(project, args.window_hours)
    for msg in messages:
        print(msg)
    return code


if __name__ == "__main__":
    sys.exit(main())
