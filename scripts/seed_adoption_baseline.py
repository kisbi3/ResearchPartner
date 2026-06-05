#!/usr/bin/env python3
"""Bridge brownfield adoption to the baseline machinery (onboarding gap ④).

In adoption mode the PI's signed ``docs/gates/adoption_decision.md`` names a
**Reproduction Baseline** — an existing result the first retrofit must reproduce.
That is exactly the baseline-strategy "Variation" path (reproduce a specific
prior result). But nothing carried it into the baseline machinery, so the chosen
baseline never became a tracked target and the Baseline gate had no entry to flip
to ``pass``.

This helper closes that gap. It reads the signed adoption decision and drafts,
non-destructively and idempotently:

  * ``docs/plan/baseline_strategy.md`` — a Variation-path note pointing at the
    chosen reproduction target (only if the file is absent);
  * ``docs/gates/baseline_registry.md`` — a ``reproduction`` row with
    ``Status=planned`` (appended once; never duplicated, never overwriting an
    existing row).

It does NOT mark anything passed: the lab reproduces the result and flips the
row to ``pass`` (which opens the Baseline gate), then marks the artifact
``validated`` in ``docs/adoption/existing_results_inventory.md`` (which lifts the
gap ③ claim-ceiling block). The brake is preserved — you must really reproduce.

Read-only over project source; it only writes the two planning/gate artifacts
above and refuses to clobber existing content.

Exit codes:
    0  seeded (or already present — nothing to do)
    1  not in adoption mode, or no reproduction baseline named
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import _project_root as project_root_mod  # noqa: E402
from _layout import (  # noqa: E402
    adoption_decision as _adoption_decision,
    baseline_registry as _baseline_registry,
    baseline_strategy as _baseline_strategy,
)
from check_adoption_recorded import is_adoption_mode  # noqa: E402

REGISTRY_HEADER = "| Date | Kind | Target | Status | Notes |"
REGISTRY_SEP = "|---|---|---|---|---|"


def _section_lines(text: str, heading: str) -> list[str]:
    """Real (non-comment, non-empty) lines under a `## heading` until the next heading."""
    out: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.strip() == heading:
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") or line.startswith("# "):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                out.append(stripped)
    return out


def reproduction_target(project: Path) -> str:
    """The one-line reproduction-baseline target named in the adoption decision."""
    decision = _adoption_decision(project)
    if not decision.exists():
        return ""
    lines = _section_lines(decision.read_text(encoding="utf-8"), "## Reproduction Baseline")
    return " ".join(lines).strip()


def _today() -> str:
    return datetime.date.today().isoformat()


def seed_baseline_strategy(project: Path, target: str) -> str:
    path = _baseline_strategy(project)
    if path.exists():
        return f"skipped (exists): {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Baseline Strategy\n\n"
        "## Path\n\n"
        "Variation (brownfield adoption) — the first verification target is to "
        "reproduce an existing result accepted in the adoption decision.\n\n"
        "## Reproduction Target\n\n"
        f"- {target}\n\n"
        "## Pass Criterion\n\n"
        "<!-- State the quantitative match (number / curve / phase boundary) that "
        "counts as a successful reproduction. -->\n",
        encoding="utf-8",
    )
    return f"wrote: {path}"


def seed_baseline_registry(project: Path, target: str) -> str:
    path = _baseline_registry(project)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Baseline Registry\n"
    if target and target in existing:
        return f"skipped (target already registered): {path}"

    row = f"| {_today()} | reproduction | {target} | planned | adopted result — reproduce, then flip to pass |"
    parts = [existing.rstrip("\n")]
    if REGISTRY_HEADER not in existing:
        parts.append("")
        parts.append(REGISTRY_HEADER)
        parts.append(REGISTRY_SEP)
    parts.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return f"wrote reproduction row: {path}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not is_adoption_mode(project):
        print(
            "Not in adoption mode — no signed docs/gates/adoption_decision.md. "
            "This helper only applies to brownfield onboarding.",
            file=sys.stderr,
        )
        return 1

    target = reproduction_target(project)
    if not target:
        print(
            "Adoption decision is signed but '## Reproduction Baseline' is empty. "
            "Have the PI name the existing result the first retrofit must reproduce, "
            "then re-run.",
            file=sys.stderr,
        )
        return 1

    print(seed_baseline_strategy(project, target))
    print(seed_baseline_registry(project, target))
    print(
        "Next: reproduce the target, flip its baseline_registry Status to `pass` "
        "(opens the Baseline gate), and mark the artifact `validated` in "
        "docs/adoption/existing_results_inventory.md (lifts the claim-ceiling block)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
