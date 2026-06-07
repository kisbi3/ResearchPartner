#!/usr/bin/env python3
"""Archive closed entries from an accumulating Markdown-table log.

Logs like `docs/logs/anomaly_log.md`, `docs/decision_log.md`, and
`docs/process/research_retrospective.md` grow monotonically over a long
research project. Each row eventually ends up `resolved`, `deferred`,
`deprecated`, `revised`, or otherwise closed — but it still sits in the
live log, inflating every read.

This script splits a log file at its Markdown table, partitions the data
rows by the Status column, keeps rows whose status matches `--keep` (default
``open|active``), and moves the rest to a dated archive file under
``docs/archive/`` (or a custom ``--archive-dir``).

The header, separator, and any post-table prose (the `## Rules` section,
etc.) stay in place. The archive is append-only — re-running on the same day
appends rather than overwriting, so rotation is safe to repeat.

Usage:
    python .harness/scripts/rotate_log.py --log docs/logs/anomaly_log.md
    python .harness/scripts/rotate_log.py --log docs/decision_log.md --status-column Status \\
        --keep "open|active|in_review" --dry-run

Recommended trigger: when the log exceeds ~50 entries, or at the end of a
research stage as part of the Stage Checkpoint workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


TABLE_SEP_RE = re.compile(r"^\s*\|\s*[-:]+(?:\s*\|\s*[-:]+)*\s*\|\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def split_log(text: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (preamble, header_lines, data_rows, trailer).

    preamble: everything before the table (including the header row line up
              to but not including the separator line).
    header_lines: [the header row line, the separator line]
    data_rows: the remaining table rows after the separator
    trailer: everything after the table block
    """
    lines = text.splitlines()
    sep_idx: int | None = None
    for i, line in enumerate(lines):
        if TABLE_SEP_RE.match(line):
            sep_idx = i
            break
    if sep_idx is None or sep_idx == 0:
        raise ValueError("No Markdown table header+separator found in log")
    header_row = lines[sep_idx - 1]
    separator = lines[sep_idx]
    preamble = lines[: sep_idx - 1]
    data_rows: list[str] = []
    trailer_start = sep_idx + 1
    for j in range(sep_idx + 1, len(lines)):
        if TABLE_ROW_RE.match(lines[j]):
            data_rows.append(lines[j])
            trailer_start = j + 1
        else:
            # Once we hit a non-row line, the table block is done.
            trailer_start = j
            break
    else:
        trailer_start = len(lines)
    trailer = lines[trailer_start:]
    return preamble, [header_row, separator], data_rows, trailer


def parse_header_columns(header_row: str) -> list[str]:
    cells = [c.strip() for c in header_row.strip().strip("|").split("|")]
    return cells


def row_cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def row_is_placeholder(cells: list[str]) -> bool:
    """Return True for empty-template rows like 'AN-001 | YYYY-MM-DD | ...'."""
    joined = " ".join(cells).strip()
    if not joined:
        return True
    # Treat YYYY-MM-DD literal as a placeholder marker.
    return "YYYY-MM-DD" in joined and not any(
        re.match(r"^\d{4}-\d{2}-\d{2}", c) for c in cells
    )


def partition_rows(
    data_rows: list[str], columns: list[str], status_column: str, keep_pattern: re.Pattern[str]
) -> tuple[list[str], list[str], list[str]]:
    """Return (kept, archived, placeholders)."""
    try:
        status_idx = [c.lower() for c in columns].index(status_column.lower())
    except ValueError as exc:
        raise ValueError(
            f"Status column {status_column!r} not found in header {columns!r}"
        ) from exc
    kept: list[str] = []
    archived: list[str] = []
    placeholders: list[str] = []
    for row in data_rows:
        cells = row_cells(row)
        if row_is_placeholder(cells):
            placeholders.append(row)
            continue
        if status_idx >= len(cells):
            kept.append(row)
            continue
        status_value = cells[status_idx]
        if keep_pattern.search(status_value):
            kept.append(row)
        else:
            archived.append(row)
    return kept, archived, placeholders


def build_archive_block(
    *,
    source: Path,
    header_lines: list[str],
    archived_rows: list[str],
    archived_on: str,
) -> str:
    lines = [
        f"# Archive of {source.name}",
        "",
        f"- Source: `{source.as_posix()}`",
        f"- Archived on: {archived_on}",
        f"- Rows in this archive: {len(archived_rows)}",
        "",
        header_lines[0],
        header_lines[1],
    ]
    lines.extend(archived_rows)
    lines.append("")
    return "\n".join(lines)


def append_to_archive(archive_path: Path, block: str) -> None:
    if archive_path.exists():
        existing = archive_path.read_text(encoding="utf-8").rstrip()
        archive_path.write_text(existing + "\n\n---\n\n" + block, encoding="utf-8")
    else:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_text(block, encoding="utf-8")


def rewrite_log(
    log_path: Path,
    preamble: list[str],
    header_lines: list[str],
    kept_rows: list[str],
    placeholders: list[str],
    trailer: list[str],
) -> None:
    parts: list[str] = []
    parts.extend(preamble)
    parts.extend(header_lines)
    # Keep placeholder template rows in the live file so the template stays usable.
    parts.extend(placeholders)
    parts.extend(kept_rows)
    parts.extend(trailer)
    log_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def rotate(
    *,
    log_path: Path,
    status_column: str,
    keep_pattern: re.Pattern[str],
    archive_dir: Path,
    dry_run: bool,
    keep_min: int,
) -> tuple[int, int, Path | None]:
    text = log_path.read_text(encoding="utf-8")
    preamble, header_lines, data_rows, trailer = split_log(text)
    columns = parse_header_columns(header_lines[0])
    kept, archived, placeholders = partition_rows(
        data_rows, columns, status_column, keep_pattern
    )
    if not archived:
        return (len(kept), 0, None)
    if len(kept) < keep_min:
        raise RuntimeError(
            f"refusing to rotate: would leave only {len(kept)} kept rows "
            f"(min {keep_min}). Use --keep-min 0 to override."
        )
    today = dt.date.today().isoformat()
    archive_path = archive_dir / f"{log_path.stem}-{today}.md"
    block = build_archive_block(
        source=log_path,
        header_lines=header_lines,
        archived_rows=archived,
        archived_on=today,
    )
    if dry_run:
        print(f"[dry-run] would archive {len(archived)} row(s) to {archive_path}")
        print(f"[dry-run] would keep {len(kept)} row(s) (+ {len(placeholders)} placeholder)")
        return (len(kept), len(archived), archive_path)
    append_to_archive(archive_path, block)
    rewrite_log(log_path, preamble, header_lines, kept, placeholders, trailer)
    return (len(kept), len(archived), archive_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True, help="Path to the log file.")
    parser.add_argument(
        "--status-column",
        type=str,
        default="Status",
        help="Name of the status column in the table header (case-insensitive).",
    )
    parser.add_argument(
        "--keep",
        type=str,
        default=r"open|active|in[_\s]?review|pending",
        help="Regex (case-insensitive); rows whose status matches stay in the live log.",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=None,
        help="Directory for archive files (default: <log-parent>/archive/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without modifying any file.",
    )
    parser.add_argument(
        "--keep-min",
        type=int,
        default=1,
        help="Refuse to rotate if fewer than this many rows would remain (default: 1).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_path: Path = args.log.resolve()
    if not log_path.is_file():
        print(f"error: log not found: {log_path}", file=sys.stderr)
        return 2
    archive_dir = (args.archive_dir or (log_path.parent / "archive")).resolve()
    keep_pattern = re.compile(args.keep, re.IGNORECASE)
    try:
        kept, archived, archive_path = rotate(
            log_path=log_path,
            status_column=args.status_column,
            keep_pattern=keep_pattern,
            archive_dir=archive_dir,
            dry_run=args.dry_run,
            keep_min=args.keep_min,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if archived == 0:
        print(f"no rows matched archive criteria; {kept} kept")
        return 0
    if args.dry_run:
        return 0
    print(f"archived {archived} row(s) to {archive_path}; {kept} kept in {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
