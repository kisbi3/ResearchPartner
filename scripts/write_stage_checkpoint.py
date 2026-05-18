#!/usr/bin/env python3
"""Write a compact Stage N Checkpoint file at the end of a research stage.

Long runs accumulate large stage outputs (raw JSON results, per-model fits,
per-trial logs). Loading those into a downstream-stage agent's context wastes
tokens and re-injects the same data repeatedly. The stage checkpoint is a
compact (<~60 lines) hand-off file that the next stage's agent reads
*instead of* the raw outputs. The raw outputs stay on disk and are loaded
only when a specific number needs deeper inspection.

This script writes the scaffold at `<run>/docs/checkpoints/stage_N_checkpoint.md`
with the date, stage number, an auto-detected listing of files under
`outputs/`, and the fixed checkpoint sections. The user fills in the summary
fields after the Stage Completion Meeting.

Usage:
    python scripts/write_stage_checkpoint.py --project <project-dir> --stage 2 \
        [--title "Synthetic-data experiments"] [--force]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


RESPAWN_WARN_THRESHOLD = 3  # >=3 spawns for the same file is a quality flag

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402


def detect_lineage_coverage(run_dir: Path) -> dict:
    """Run the lineage coverage gate and summarize for the checkpoint.

    Returns a dict with `violation_count`, `violations` (list), and a
    short human-readable `status` string. Failure to import the checker
    or read the run's JSON degrades to status="skipped" rather than
    breaking the stage checkpoint flow.
    """
    try:
        import check_lineage_coverage as clc  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        return {"violation_count": 0, "violations": [],
                "status": f"skipped (import failed: {exc})"}
    try:
        violations = clc.check(run_dir)
    except Exception as exc:  # noqa: BLE001
        return {"violation_count": 0, "violations": [],
                "status": f"skipped (check failed: {exc})"}
    if not violations:
        return {"violation_count": 0, "violations": [],
                "status": "pass — all skill-required lineage edges are present"}
    return {"violation_count": len(violations), "violations": violations,
            "status": f"{len(violations)} violation(s) — see check_lineage_coverage.py"}


def detect_cross_tier_compliance(run_dir: Path) -> dict:
    """Count src/*.py files vs Implementation Agent spawn log entries.

    Also counts re-spawns per file: multiple Implementation Agent rows
    pointing at the same File cell mean the Graduate Student review
    rejected earlier versions. A high re-spawn count is a quality signal
    (poor spec, ambiguous task, or buggy Implementation Agent output).
    """
    src_dir = run_dir / "src"
    src_files = sorted(src_dir.glob("*.py")) if src_dir.is_dir() else []
    src_count = len(src_files)

    spawn_log = run_dir / "docs" / "gates" / "agent_spawn_log.md"
    impl_spawns = 0
    spawns_per_file: dict[str, int] = {}
    has_log = spawn_log.is_file()
    if has_log:
        for line in spawn_log.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[1].lower() == "implementation" and cells[0] != "Date":
                impl_spawns += 1
                file_cell = cells[2]
                spawns_per_file[file_cell] = spawns_per_file.get(file_cell, 0) + 1

    # Files that needed >= RESPAWN_WARN_THRESHOLD spawns
    respawn_hotspots = sorted(
        ((f, n) for f, n in spawns_per_file.items() if n >= RESPAWN_WARN_THRESHOLD),
        key=lambda kv: -kv[1],
    )
    # Distinct files with at least one spawn record
    distinct_impl_files = len(spawns_per_file)

    if not has_log and src_count == 0:
        status = "— no src/ files and no spawn log"
        verdict = "n/a"
    elif not has_log:
        status = f"⚠ {src_count} src/ file(s) found but no spawn log — compliance unknown"
        verdict = "unknown"
    elif src_count == 0:
        status = "— no src/ files in this stage"
        verdict = "n/a"
    elif distinct_impl_files >= src_count:
        # Distinct file coverage is the right comparison — re-spawns are normal
        if respawn_hotspots:
            hot_str = ", ".join(f"{f}×{n}" for f, n in respawn_hotspots)
            status = (
                f"✓ all {src_count} src/ file(s) have spawn records "
                f"(total {impl_spawns} spawns); re-spawn hotspots: {hot_str}"
            )
        else:
            status = f"✓ all {src_count} src/ file(s) have spawn records (total {impl_spawns} spawns)"
        verdict = "pass"
    else:
        gap = src_count - distinct_impl_files
        status = (
            f"⚠ {gap} src/ file(s) may have been written directly "
            f"(distinct files in spawn log {distinct_impl_files} < src files {src_count})"
        )
        verdict = "warn"

    return {
        "src_count": src_count,
        "impl_spawns": impl_spawns,
        "distinct_impl_files": distinct_impl_files,
        "respawn_hotspots": respawn_hotspots,
        "has_log": has_log,
        "status": status,
        "verdict": verdict,
    }


def discover_outputs(run_dir: Path, limit: int = 40) -> list[tuple[str, int]]:
    outputs = run_dir / "outputs"
    if not outputs.is_dir():
        return []
    entries: list[tuple[str, int]] = []
    for path in sorted(outputs.rglob("*")):
        if path.is_file():
            try:
                rel = path.relative_to(run_dir).as_posix()
            except ValueError:
                rel = path.as_posix()
            entries.append((rel, path.stat().st_size))
        if len(entries) >= limit:
            entries.append(("…", -1))
            break
    return entries


def format_size(n: int) -> str:
    if n < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n //= 1024
    return f"{n} TB"


def build_checkpoint(
    *,
    run_dir: Path,
    stage: int,
    title: str,
    today: str,
    outputs: list[tuple[str, int]],
    compliance: dict,
    lineage_block: str = "Status: — lineage check skipped",
) -> str:
    title_line = f"Stage {stage}" + (f" — {title}" if title else "")
    output_table = ["| File | Size |", "|---|---|"]
    if not outputs:
        output_table.append("| _(no outputs/ files discovered)_ | — |")
    else:
        for rel, size in outputs:
            output_table.append(f"| `{rel}` | {format_size(size)} |")
    return f"""# {title_line} Checkpoint

This is the compact hand-off for Stage {stage}. The next-stage agent should
load **this file only** for routine work and open raw outputs (listed below)
only when a specific value needs deeper inspection.

- Run directory: `{run_dir.as_posix()}`
- Stage: {stage}
- Completion date: {today}
- Generator: `scripts/write_stage_checkpoint.py`

## Stage Gate

- Status: <pass / partial / fail / waived>
- Waiver (if any): <link to waiver file or `none`>
- Claim ceiling after this stage: <observation / interpretation / mechanism / generalization / unsupported>
- Stage Completion Meeting record: <link to docs/process/research_retrospective.md section>

## Inputs Consumed

- <file or stage referenced>:
- <file or stage referenced>:

## Outputs Produced

{chr(10).join(output_table)}

## Key Numbers (max ~10 scalars)

| Quantity | Value | Units | Source File |
|---|---|---|---|
|  |  |  |  |

## One-Paragraph Result

<2–4 sentences summarizing what this stage established. No interpretation
beyond what the evidence supports. Mark unsupported wording as `확인 필요`.>

## What the Next Stage Should Load

List ≤ 3 files (this checkpoint + at most two others). If more are needed,
the design is too coupled and the stage boundary should be reconsidered.

1. `docs/checkpoints/stage_{stage}_checkpoint.md` (this file)
2.
3.

## Open Questions / Anomalies Carried Forward

- <one bullet per unresolved item; link to anomaly log entry if any>

## Cross-Tier Compliance

| Metric | Count |
|---|---|
| `src/*.py` files this stage | {compliance['src_count']} |
| Distinct src files in spawn log | {compliance.get('distinct_impl_files', 0)} |
| Implementation Agent spawns total | {compliance['impl_spawns']} |
| Re-spawn hotspots (≥{RESPAWN_WARN_THRESHOLD} spawns/file) | {len(compliance.get('respawn_hotspots', []))} |

Status: {compliance['status']}

> Every `src/` file must be written by a spawned Implementation Agent — not
> by the Lead Agent and not by a Graduate Student (who reviews code but
> never writes it). Spawn records are in `docs/gates/agent_spawn_log.md`.
> Re-spawns are normal (the Graduate Student review can reject a draft),
> but a hotspot with ≥{RESPAWN_WARN_THRESHOLD} spawns on one file signals a
> poor spec, an ambiguous task, or a buggy Implementation Agent pass —
> worth inspecting at this stage gate. Verdict: **{compliance['verdict']}**.

## Lineage Coverage

{lineage_block}

> Auto-seeded lineage nodes (papers / model versions / claims / figures /
> anomalies) without their skill-required cross-referential edges are silent
> failures — the Lineage tab still renders the node but shows it as
> unanchored. The coverage gate (`scripts/check_lineage_coverage.py --run
> <run-dir>`) lists every node missing an edge a skill said to emit. Fix
> each row before promoting the run's claim ceiling.

## Notes for Reuse

- Reusable artifacts: <scripts, recipes, benchmarks created in this stage>
- Negative results worth remembering: <what failed and why>
"""


def _format_lineage_block(lineage: dict) -> str:
    if lineage.get("violation_count", 0) == 0:
        return f"Status: {lineage['status']}"
    lines = [f"Status: {lineage['status']}", "", "| Node | Kind | Missing |", "|---|---|---|"]
    for v in lineage["violations"]:
        rule_short = v["rule"].replace("|", "\\|")
        lines.append(f"| `{v['node_id']}` | {v['lineage_kind']} | {rule_short} |")
    return "\n".join(lines)


def write_checkpoint(*, run_dir: Path, stage: int, title: str, force: bool, skip_compliance: bool = False) -> Path:
    checkpoints = run_dir / "docs" / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    output = checkpoints / f"stage_{stage}_checkpoint.md"
    if output.exists() and not force:
        raise FileExistsError(f"{output} already exists (use --force to overwrite)")
    today = dt.date.today().isoformat()
    outputs = discover_outputs(run_dir)
    compliance = (
        {"src_count": 0, "impl_spawns": 0, "has_log": False,
         "status": "— compliance check skipped (--no-compliance)", "verdict": "skipped"}
        if skip_compliance
        else detect_cross_tier_compliance(run_dir)
    )
    lineage = (
        {"violation_count": 0, "violations": [],
         "status": "— lineage check skipped (--no-compliance)"}
        if skip_compliance
        else detect_lineage_coverage(run_dir)
    )
    output.write_text(
        build_checkpoint(
            run_dir=run_dir,
            stage=stage,
            title=title,
            today=today,
            outputs=outputs,
            compliance=compliance,
            lineage_block=_format_lineage_block(lineage),
        ),
        encoding="utf-8",
    )
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", "--run",
        dest="project",
        type=Path,
        default=None,
        help="Project root directory. Default: walk up from cwd looking for "
             "the `.research-harness` marker. `--run` kept as alias for one release.",
    )
    parser.add_argument("--stage", type=int, required=True, help="Stage number (e.g. 2).")
    parser.add_argument("--title", type=str, default="", help="Optional short stage title.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing checkpoint.")
    parser.add_argument(
        "--no-compliance",
        action="store_true",
        help="Skip cross-tier compliance check (for harness-only or non-research runs).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    try:
        path = write_checkpoint(
            run_dir=project,
            stage=args.stage,
            title=args.title,
            force=args.force,
            skip_compliance=args.no_compliance,
        )
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
