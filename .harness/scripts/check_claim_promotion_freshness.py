#!/usr/bin/env python3
"""Claim promotion freshness gate.

When a claim file under ``docs/claims/`` is written/edited with a non-
``observation`` ceiling (or ``status: promoted``), every output artifact it
cites (``outputs/figures/...``, ``outputs/data/...``, ``outputs/tables/...``)
must exist on disk and have been modified within the freshness window
(default 24 h). Mechanism/generalization claim files must also contain a
resolved finding lifecycle with direct-read evidence paths.

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
    0 — pass / skip (no promoted claim, all citations fresh, lifecycle valid)
    1 — fail (stale/missing references or invalid finding lifecycle)
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
from check_adoption_recorded import is_adoption_mode  # noqa: E402

# Brownfield adoption (gap ③): adopted artifacts carry a Validation Status in
# docs/adoption/existing_results_inventory.md. A promoted claim may only lean on
# an adopted artifact that the PI/lab has marked `validated` (or explicitly
# `waived`). Citing an adopted artifact still at `partial`/`unknown`/`failed`/
# `deprecated` caps the claim at observation until it is reproduced and recorded.
ADOPTION_INVENTORY_REL = "docs/adoption/existing_results_inventory.md"
_KNOWN_ADOPTION_STATUSES = {
    "validated", "partial", "unknown", "failed", "waived", "deprecated",
}
# Statuses that DO let a promoted claim cite the artifact (validated, or a PI
# waiver of the risk). Everything else blocks promotion.
_ALLOWED_ADOPTION_STATUSES = {"validated", "waived"}

# ── Detection patterns ───────────────────────────────────────────────────────
# A claim is considered "promoted" if it carries any non-observation ceiling.
PROMOTED_CEILING_RE = re.compile(
    r"(?im)^\s*(?:ceiling|claim[-_\s]?ceiling|status)\s*:\s*"
    r"(interpretation|mechanism|generalization|promoted)\b"
)
CLAIM_CEILING_RE = re.compile(
    r"(?im)^\s*(?:ceiling|claim[-_\s]?ceiling)\s*:\s*"
    r"(observation|interpretation|mechanism|generalization)\b"
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
    adopted_unvalidated: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class LifecycleResult:
    status: str  # "pass" | "skip" | "fail"
    reason: str = ""
    direct_paths: list[str] = field(default_factory=list)


def _is_promoted(text: str) -> bool:
    return bool(PROMOTED_CEILING_RE.search(text))


def claim_ceiling(text: str) -> str | None:
    match = CLAIM_CEILING_RE.search(text)
    return match.group(1).lower() if match else None


def finding_lifecycle_required(text: str) -> bool:
    return claim_ceiling(text) in {"mechanism", "generalization"}


def _find_output_refs(text: str) -> list[str]:
    # De-dupe while preserving order; normalise separators.
    seen: dict[str, None] = {}
    for match in OUTPUT_REF_RE.findall(text):
        norm = match.replace("\\", "/").lstrip("./")
        seen.setdefault(norm, None)
    return list(seen.keys())


FINDING_STATES = {
    "candidate",
    "independently_checked",
    "validated_blocker",
    "validated_limitation",
    "false_alarm",
    "needs_researcher_judgment",
    "evidence_linked",
    "researcher_reviewed",
}

STATE_RE = re.compile(r"(?im)^\s*(?:status|result|decision)\s*:\s*([A-Za-z0-9_ -]+)")
DIRECT_READ_HEADING_RE = re.compile(r"(?im)^#{2,6}\s+Evidence Paths Read Directly\s*$")
HEADING_RE = re.compile(r"^#{1,6}\s+")


def _state_tokens(text: str) -> set[str]:
    states: set[str] = set()
    for match in STATE_RE.finditer(text):
        normalized = match.group(1).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in FINDING_STATES:
            states.add(normalized)
    return states


def _clean_path_token(value: str) -> str:
    token = value.strip().strip("`").strip()
    link = re.match(r"\[[^\]]+\]\(([^)]+)\)", token)
    if link:
        token = link.group(1)
    return token.strip().strip("`").strip()


def evidence_paths_read_directly(text: str) -> list[str]:
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if DIRECT_READ_HEADING_RE.match(line):
            start = index + 1
            break
    if start is None:
        return []

    paths: list[str] = []
    for line in lines[start:]:
        if HEADING_RE.match(line):
            break
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        token = _clean_path_token(stripped[1:])
        if token and "FILL IN" not in token and not token.startswith("http"):
            paths.append(token.replace("\\", "/").lstrip("./"))
    return paths


def _path_resolves_inside_project(project: Path, rel_path: str) -> bool:
    target = (project / rel_path).resolve()
    try:
        target.relative_to(project.resolve())
    except ValueError:
        return False
    return target.is_file()


def check_finding_lifecycle(
    file_path: Path,
    content: str,
    project: Path,
) -> LifecycleResult:
    """Validate the declarative finding lifecycle for mechanism/generalization.

    This intentionally verifies only structure: state tokens, declared direct-read
    paths, and whether those paths resolve to files under the project. It cannot
    and does not claim to prove that the Lead actually read the files.
    """
    if not finding_lifecycle_required(content):
        return LifecycleResult(status="skip", reason="finding lifecycle not required")

    if "Evidence Paths Read Directly" not in content or "Finding Lifecycle" not in content:
        return LifecycleResult(
            status="fail",
            reason=(
                "mechanism/generalization claims require a ## Finding Lifecycle "
                "section with ## Evidence Paths Read Directly"
            ),
        )

    states = _state_tokens(content)
    if "candidate" in states:
        return LifecycleResult(status="fail", reason="candidate finding cannot promote")
    if "false_alarm" in states:
        return LifecycleResult(status="fail", reason="false_alarm finding cannot promote")
    if "independently_checked" not in states:
        return LifecycleResult(
            status="fail",
            reason="finding lifecycle missing independently_checked state",
        )
    if "evidence_linked" not in states:
        return LifecycleResult(
            status="fail",
            reason="finding lifecycle missing evidence_linked state",
        )

    direct_paths = evidence_paths_read_directly(content)
    if not direct_paths:
        return LifecycleResult(
            status="fail",
            reason="Evidence Paths Read Directly must contain at least one project path",
        )

    unresolved = [
        path for path in direct_paths
        if not _path_resolves_inside_project(project, path)
    ]
    if unresolved:
        return LifecycleResult(
            status="fail",
            reason=(
                "Evidence Paths Read Directly contains unresolved project path(s): "
                + ", ".join(unresolved[:3])
            ),
            direct_paths=direct_paths,
        )

    return LifecycleResult(
        status="pass",
        reason=f"{len(direct_paths)} direct-read path(s) declared and resolved",
        direct_paths=direct_paths,
    )


def _extract_inventory_path(cell: str) -> str:
    """Pull a single artifact path out of an inventory 'Result/Figure' cell."""
    token = cell.strip().strip("`").strip()
    link = re.match(r"\[[^\]]+\]\(([^)]+)\)", token)
    if link:
        token = link.group(1)
    return token.strip().strip("`").strip().replace("\\", "/").lstrip("./")


def _adopted_artifact_statuses(project: Path) -> dict[str, str]:
    """Map adopted artifact path → validation status from the results inventory.

    Parses the markdown table in docs/adoption/existing_results_inventory.md,
    locating the artifact column ("Result"/"Figure"/"Table") and the
    "Validation Status" column by header name. Rows whose status cell still holds
    the multi-option template placeholder (more than one known status token) are
    skipped — they carry no real status yet.
    """
    path = project / ADOPTION_INVENTORY_REL
    if not path.is_file():
        return {}
    statuses: dict[str, str] = {}
    art_col: int | None = None
    stat_col: int | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "|" not in line:
            continue
        if set(line.strip()) <= set("|-: "):  # separator row
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        lowered = [c.lower() for c in cells]
        if art_col is None:
            if any("validation status" in c for c in lowered) and any(
                ("result" in c or "figure" in c or "table" in c) for c in lowered
            ):
                art_col = next(
                    i for i, c in enumerate(lowered)
                    if "result" in c or "figure" in c or "table" in c
                )
                stat_col = next(i for i, c in enumerate(lowered) if "validation status" in c)
            continue
        if stat_col is None or art_col >= len(cells) or stat_col >= len(cells):
            continue
        tokens = [t for t in re.split(r"[\s/,]+", lowered[stat_col]) if t in _KNOWN_ADOPTION_STATUSES]
        if len(tokens) != 1:  # 0 = free text / blank, >1 = template placeholder
            continue
        artifact = _extract_inventory_path(cells[art_col])
        if artifact:
            statuses[artifact] = tokens[0]
    return statuses


def _blocked_adopted_citations(content: str, project: Path) -> list[str]:
    """Adopted artifacts a promoted claim cites that are not validated/waived."""
    statuses = _adopted_artifact_statuses(project)
    if not statuses:
        return []
    haystack = content.replace("\\", "/")
    blocked: list[str] = []
    for artifact, status in statuses.items():
        if status in _ALLOWED_ADOPTION_STATUSES:
            continue
        basename = artifact.rsplit("/", 1)[-1]
        if artifact in haystack or (basename and basename in haystack):
            blocked.append(f"{artifact} ({status})")
    return blocked


def check_claim_freshness(
    file_path: Path,
    content: str,
    project: Path,
    window_hours: int = 24,
) -> FreshnessResult:
    """Return a FreshnessResult for *content* (intended write/edit body)."""
    if not _is_promoted(content):
        return FreshnessResult(status="skip", reason="not a promoted claim")

    # Gap ③: in adoption mode, block promotion that leans on an adopted artifact
    # not yet validated. Checked before the finding-lifecycle check so the
    # specific adoption reason surfaces at any promoted ceiling. (No-op for
    # greenfield projects — is_adoption_mode False.)
    if is_adoption_mode(project):
        blocked = _blocked_adopted_citations(content, project)
        if blocked:
            return FreshnessResult(
                status="fail",
                adopted_unvalidated=blocked,
                reason=(
                    "promoted claim cites adopted artifact(s) not yet validated: "
                    + ", ".join(blocked[:3])
                    + " — reproduce and record the result in baseline_registry.md "
                    "(mark it validated in the adoption inventory), or lower the "
                    "ceiling to observation."
                ),
            )

    lifecycle = check_finding_lifecycle(file_path, content, project)
    if lifecycle.status == "fail":
        return FreshnessResult(status="fail", reason=lifecycle.reason)

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
            if result.adopted_unvalidated:
                detail.append("adopted-unvalidated=" + ", ".join(result.adopted_unvalidated[:3]))
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
