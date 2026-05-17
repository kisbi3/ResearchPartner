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
    python scripts/write_stage_checkpoint.py --run <run-dir> --stage 2 \
        [--title "Synthetic-data experiments"] [--force]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


def detect_cross_tier_compliance(run_dir: Path) -> dict:
    """Count src/*.py files vs Implementation Agent spawn log entries."""
    src_dir = run_dir / "src"
    src_files = sorted(src_dir.glob("*.py")) if src_dir.is_dir() else []
    src_count = len(src_files)

    spawn_log = run_dir / "docs" / "gates" / "agent_spawn_log.md"
    impl_spawns = 0
    has_log = spawn_log.is_file()
    if has_log:
        for line in spawn_log.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1].lower() == "implementation" and cells[0] != "Date":
                impl_spawns += 1

    if not has_log and src_count == 0:
        status = "— no src/ files and no spawn log"
        verdict = "n/a"
    elif not has_log:
        status = f"⚠ {src_count} src/ file(s) found but no spawn log — compliance unknown"
        verdict = "unknown"
    elif src_count == 0:
        status = "— no src/ files in this stage"
        verdict = "n/a"
    elif impl_spawns >= src_count:
        status = f"✓ {impl_spawns} Implementation Agent spawn(s) ≥ {src_count} src/ file(s)"
        verdict = "pass"
    else:
        gap = src_count - impl_spawns
        status = (
            f"⚠ {gap} src/ file(s) may have been written directly "
            f"(spawns {impl_spawns} < files {src_count})"
        )
        verdict = "warn"

    return {
        "src_count": src_count,
        "impl_spawns": impl_spawns,
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
| Implementation Agent spawns (spawn log) | {compliance['impl_spawns']} |

Status: {compliance['status']}

> Every `src/` file should be written by a spawned Implementation Agent, not
> directly by the Professor or Graduate Student. Spawn records are in
> `docs/gates/agent_spawn_log.md`. Verdict: **{compliance['verdict']}**.

## Notes for Reuse

- Reusable artifacts: <scripts, recipes, benchmarks created in this stage>
- Negative results worth remembering: <what failed and why>
"""


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
    output.write_text(
        build_checkpoint(
            run_dir=run_dir,
            stage=stage,
            title=title,
            today=today,
            outputs=outputs,
            compliance=compliance,
        ),
        encoding="utf-8",
    )
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="Run directory.")
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
        path = write_checkpoint(
            run_dir=args.run.resolve(),
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
