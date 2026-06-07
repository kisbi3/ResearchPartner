#!/usr/bin/env python3
"""Create a lightweight intake report for an existing physics project.

This is the first step of brownfield onboarding (see
skills/existing-research-onboarding/SKILL.md). It is strictly read-only over the
project: it inventories what already exists and DRAFTS the adoption inventory
tables, but it never modifies project source, data, figures, or notes. It writes
only its own report (``--output``) and, when ``--write-drafts`` is given, opt-in
``*.draft.md`` files under ``docs/adoption/`` — and even then it refuses to
overwrite a human-edited table.

The draft inventory closes gap ② of the onboarding design: instead of handing the
researcher blank tables, the scanner pre-fills a best-effort draft — one row per
detected figure with a guessed generating script, guessed input data, detected
RNG/seed sites, config/param files, manuscript/claim files, and git recency — so
the lab corrects a draft rather than authoring from scratch. Every auto-detected
field is a GUESS to verify; nothing here is evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys


COMMON_DIRS = [
    "src",
    "scripts",
    "notebooks",
    "data",
    "results",
    "figures",
    "plots",
    "manuscript",
    "paper",
    "docs",
]

INTERESTING_SUFFIXES = {
    ".py": "python",
    ".ipynb": "notebook",
    ".tex": "tex",
    ".md": "markdown",
    ".csv": "data",
    ".tsv": "data",
    ".json": "json",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".png": "figure",
    ".jpg": "figure",
    ".jpeg": "figure",
    ".pdf": "pdf",
    ".svg": "figure",
}

HARNESS_PATHS = [
    "AGENTS.md",
    "GEMINI.md",
    "PHYSICS.md",
    "skills/baseline-validation/SKILL.md",
    "docs/baseline_registry.md",
    "docs/adoption/existing_project_intake.md",
    "docs/adoption/retrofit_validation_plan.md",
]

BANNED_MATPLOTLIB_SHOW = "plt." + "show("

IGNORED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
    ".pytest_cache", ".ipynb_checkpoints", "site-packages", ".tox", "dist",
    "build", ".eggs",
}

CODE_SUFFIXES = {".py", ".ipynb"}
FIGURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}
DATA_SUFFIXES = {".csv", ".tsv", ".h5", ".hdf5", ".npz", ".npy", ".parquet", ".feather", ".nc"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"}
MANUSCRIPT_SUFFIXES = {".tex", ".bib"}

# RNG / seed sites — the parameters most often lost when adopting old runs.
SEED_PATTERNS = [
    r"np\.random\.seed\s*\(",
    r"numpy\.random\.seed\s*\(",
    r"random\.seed\s*\(",
    r"default_rng\s*\(",
    r"RandomState\s*\(",
    r"random_state\s*=",
    r"\bseed\s*=",
    r"torch\.manual_seed\s*\(",
    r"manual_seed\s*\(",
    r"tf\.random\.set_seed\s*\(",
    r"set_seed\s*\(",
]
_SEED_RE = re.compile("|".join(SEED_PATTERNS))

# Caps so a huge project does not produce an unbounded report. Truncation is
# always reported (no silent caps).
MAX_FIGURES = 80
MAX_SEED_SITES = 60
MAX_LISTED = 60


# ── basic inventory (original behaviour, preserved) ───────────────────────────

def _walk_files(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def count_interesting_files(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in _walk_files(root):
        label = INTERESTING_SUFFIXES.get(path.suffix.lower())
        if label:
            counts[label] += 1
    return counts


def find_directories(root: Path) -> list[str]:
    return [directory for directory in COMMON_DIRS if (root / directory).is_dir()]


def find_harness_paths(root: Path) -> list[str]:
    return [path for path in HARNESS_PATHS if (root / path).exists()]


def scan_for_matplotlib_show(root: Path) -> list[str]:
    matches = []
    for directory in ["src", "scripts", "notebooks"]:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in {".py", ".ipynb"}:
                continue
            text = _safe_read(path)
            if BANNED_MATPLOTLIB_SHOW in text:
                matches.append(str(path.relative_to(root)))
    return matches


# ── draft-inventory helpers (gap ②) ───────────────────────────────────────────

def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def find_by_suffix(root: Path, suffixes: set[str]) -> list[Path]:
    found = [p for p in _walk_files(root) if p.suffix.lower() in suffixes]
    return sorted(found, key=lambda p: p.as_posix())


def read_code_texts(root: Path) -> dict[str, str]:
    """Map relative code path → text, for generator/seed guessing."""
    texts: dict[str, str] = {}
    for path in _walk_files(root):
        if path.suffix.lower() in CODE_SUFFIXES:
            texts[_rel(root, path)] = _safe_read(path)
    return texts


def guess_generators(figure: Path, root: Path, code_texts: dict[str, str]) -> list[str]:
    """Best-effort: code files that reference the figure's name → likely creator."""
    basename = figure.name
    stem = figure.stem
    strong: list[str] = []
    weak: list[str] = []
    for rel, text in code_texts.items():
        if basename in text:
            strong.append(rel)
        elif stem and stem in text and re.search(r"savefig|plt\.save|fig\.save|write_image|to_csv|imsave|saveas", text):
            weak.append(rel)
    ranked = strong + [w for w in weak if w not in strong]
    return ranked[:3]


def find_seed_sites(code_texts: dict[str, str]) -> list[tuple[str, int, str]]:
    sites: list[tuple[str, int, str]] = []
    for rel, text in code_texts.items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _SEED_RE.search(line):
                snippet = line.strip()
                if len(snippet) > 100:
                    snippet = snippet[:97] + "…"
                sites.append((rel, lineno, snippet))
    return sites


def git_last_modified(root: Path, rel: str) -> str:
    """Best-effort last-commit date (YYYY-MM-DD); falls back to file mtime."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%cs", "--", rel],
            capture_output=True, text=True, timeout=10,
        )
        out = (proc.stdout or "").strip()
        if proc.returncode == 0 and out:
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        import datetime
        ts = (root / rel).stat().st_mtime
        return datetime.date.fromtimestamp(ts).isoformat() + " (mtime)"
    except OSError:
        return "unknown"


# ── draft builders ─────────────────────────────────────────────────────────────

def build_results_inventory_draft(root: Path, code_texts: dict[str, str]) -> str:
    figures = find_by_suffix(root, FIGURE_SUFFIXES)
    data_files = find_by_suffix(root, DATA_SUFFIXES)
    data_rels = [_rel(root, d) for d in data_files]

    truncated = len(figures) > MAX_FIGURES
    shown = figures[:MAX_FIGURES]

    lines = [
        "# Existing Results Inventory — DRAFT (auto-detected, verify before trusting)",
        "",
        "<!-- Generated by .harness/scripts/audit_existing_project.py. Every field is a GUESS,",
        "     not evidence. Correct it, then copy verified rows into",
        "     docs/adoption/existing_results_inventory.md and have the PI sign the",
        "     adoption decision. Validation Status starts at `unknown` on purpose. -->",
        "",
        "| ID | Result / Figure | Guessed Source Script | Guessed Input Data | Last Modified | Validation Status | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    if not shown:
        lines.append("| ER-001 |  |  |  |  | unknown | no figures detected |")
    for idx, fig in enumerate(shown, start=1):
        rel = _rel(root, fig)
        gens = guess_generators(fig, root, code_texts)
        gen_cell = "<br>".join(f"`{g}`" for g in gens) if gens else "— (not found)"
        # crude data guess: data files sharing the figure stem
        stem = fig.stem.lower()
        data_guess = [f"`{d}`" for d in data_rels if stem and stem in Path(d).stem.lower()][:2]
        data_cell = "<br>".join(data_guess) if data_guess else "—"
        when = git_last_modified(root, rel)
        lines.append(
            f"| ER-{idx:03d} | `{rel}` | {gen_cell} | {data_cell} | {when} | unknown | auto-detected — verify |"
        )
    if truncated:
        lines.append("")
        lines.append(f"> NOTE: {len(figures)} figures detected; only the first {MAX_FIGURES} are listed.")
    return "\n".join(lines) + "\n"


def build_signals_section(root: Path, code_texts: dict[str, str]) -> str:
    seed_sites = find_seed_sites(code_texts)
    configs = find_by_suffix(root, CONFIG_SUFFIXES)
    manuscripts = find_by_suffix(root, MANUSCRIPT_SUFFIXES)
    data_files = find_by_suffix(root, DATA_SUFFIXES)

    lines: list[str] = ["## Detected RNG / Seed Sites (verify — parameters often lost on adoption)", ""]
    if seed_sites:
        for rel, lineno, snippet in seed_sites[:MAX_SEED_SITES]:
            lines.append(f"- `{rel}:{lineno}` — `{snippet}`")
        if len(seed_sites) > MAX_SEED_SITES:
            lines.append(f"- … {len(seed_sites) - MAX_SEED_SITES} more seed/RNG sites not listed")
    else:
        lines.append("- None detected (no explicit seed/RNG calls found — runs may be non-reproducible)")

    def _block(title: str, paths: list[Path], note: str) -> None:
        lines.extend(["", f"## {title}", ""])
        if paths:
            for p in paths[:MAX_LISTED]:
                lines.append(f"- `{_rel(root, p)}`")
            if len(paths) > MAX_LISTED:
                lines.append(f"- … {len(paths) - MAX_LISTED} more not listed")
        else:
            lines.append(f"- {note}")

    _block("Config / Parameter Files", configs, "None detected")
    _block("Manuscript / Bibliography Files", manuscripts, "None detected (.tex/.bib)")
    _block("Data Files", data_files, "None detected")
    return "\n".join(lines) + "\n"


def build_intake_draft(root: Path, counts: Counter[str]) -> str:
    has_git = (root / ".git").exists()
    return (
        "# Existing Project Intake — DRAFT (auto-detected, complete by hand)\n"
        "\n"
        "<!-- Generated by .harness/scripts/audit_existing_project.py. The scanner cannot\n"
        "     infer the research question, the model, or the current stage — fill\n"
        "     those in. Then copy into docs/adoption/existing_project_intake.md. -->\n"
        "\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| Project name | `{root.name}` |\n"
        "| Research question / working hypothesis | _(fill in — not auto-detectable)_ |\n"
        "| Physical system | _(fill in)_ |\n"
        "| Main model(s) | _(fill in)_ |\n"
        "| Current stage | exploratory / validation / production runs / manuscript / revision |\n"
        f"| Version control | {'git present' if has_git else 'no git metadata'} |\n"
        f"| Code files | {counts.get('python', 0)} python, {counts.get('notebook', 0)} notebooks |\n"
        f"| Figures | {counts.get('figure', 0)} |\n"
        f"| Data files | {counts.get('data', 0)} |\n"
        "| Primary researcher decision needed | _(fill in)_ |\n"
    )


# ── report assembly ────────────────────────────────────────────────────────────

def make_report(root: Path, *, with_drafts: bool = True) -> str:
    directories = find_directories(root)
    counts = count_interesting_files(root)
    harness = find_harness_paths(root)
    show_matches = scan_for_matplotlib_show(root)
    has_git = (root / ".git").exists()

    lines = [
        "# Existing Project Audit",
        "",
        f"- Root: `{root}`",
        f"- Git metadata present: {'yes' if has_git else 'no'}",
        "",
        "## Common Directories",
        "",
    ]
    if directories:
        lines.extend(f"- `{directory}/`" for directory in directories)
    else:
        lines.append("- None detected")

    lines.extend(["", "## File Type Counts", ""])
    if counts:
        for label, count in sorted(counts.items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No common research file types detected")

    lines.extend(["", "## Harness Files Present", ""])
    if harness:
        lines.extend(f"- `{path}`" for path in harness)
    else:
        lines.append("- No harness files detected")

    lines.extend(["", "## Potential Issues", ""])
    if show_matches:
        lines.append(f"- Found direct `{BANNED_MATPLOTLIB_SHOW})` usage in:")
        lines.extend(f"  - `{path}`" for path in show_matches)
    else:
        lines.append("- No direct matplotlib show calls detected in common code directories")

    if with_drafts:
        code_texts = read_code_texts(root)
        lines.extend([
            "",
            "---",
            "",
            "## Draft Inventory (auto-detected — verify before trusting)",
            "",
            "The rows below are a best-effort draft to correct, not evidence. "
            "Source-script and input-data columns are guesses from filename "
            "references; confirm each before copying into the adoption tables.",
            "",
            build_results_inventory_draft(root, code_texts),
            "",
            build_signals_section(root, code_texts),
        ])

    lines.extend(
        [
            "",
            "## Suggested First Retrofit Target",
            "",
            "Choose one narrow target: reproduce one existing figure, validate one toy model, audit one simulation pipeline, or map one manuscript section to evidence.",
            "",
            "Then fill docs/adoption/* and have the PI sign docs/gates/adoption_decision.md.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_draft_if_absent(path: Path, content: str) -> str:
    """Write a draft file but never clobber a human-edited one. Returns a status."""
    if path.exists():
        return f"skipped (exists): {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"wrote: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit an existing physics project before attaching the research harness."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to audit. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a markdown report. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--no-drafts",
        action="store_true",
        help="Skip the auto-detected draft inventory (faster; basic audit only).",
    )
    parser.add_argument(
        "--write-drafts",
        action="store_true",
        help="Also write docs/adoption/{existing_results_inventory,existing_project_intake}.draft.md "
             "(never overwrites an existing file).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    report = make_report(root, with_drafts=not args.no_drafts)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)

    if args.write_drafts:
        code_texts = read_code_texts(root)
        counts = count_interesting_files(root)
        adoption = root / "docs" / "adoption"
        results = _write_draft_if_absent(
            adoption / "existing_results_inventory.draft.md",
            build_results_inventory_draft(root, code_texts) + "\n" + build_signals_section(root, code_texts),
        )
        intake = _write_draft_if_absent(
            adoption / "existing_project_intake.draft.md",
            build_intake_draft(root, counts),
        )
        print(f"\n[draft] {results}", file=sys.stderr)
        print(f"[draft] {intake}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
