#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands that write code into a run directory.

The Write/Edit cross-tier hook (check_src_write_authorization.py) covers the
Write and Edit tools, but a Bash command can write a file too —
``echo ... > sim.py``, ``cat <<EOF > sim.py``, ``sed -i ... sim.py``,
``cp other.py <run>/src/sim.py``, ``python -c "open('sim.py','w')..."``,
``Set-Content`` / ``Out-File`` in PowerShell, and so on. Without this hook,
Bash would be a wide-open back door around the "Graduate Students and the
Lead Agent do not write code" rule.

This hook inspects the Bash ``command`` string for patterns that look like
they could create or modify a ``.py`` or ``.ipynb`` file inside a
``ResearchPartner-runs/<run>/`` directory (excluding ``<run>/docs/`` and
``<run>/literature/``, same as the Write/Edit hook).

Detection is intentionally conservative (false positives are blocked, not
false negatives) — when in doubt the user can set
``RESEARCH_HARNESS_BYPASS_SRC_GATE=1`` (the same bypass as the Write/Edit
hook) for an explicit one-off waiver.

Exit codes:
- 0: command does not look like a covered code write
- 2: command looks like a code write to a covered run path
"""

from __future__ import annotations

import json
import os
import re
import sys

COVERED_EXTENSIONS = (".py", ".ipynb")
EXEMPT_SUBDIRS = ("/docs/", "/literature/", "\\docs\\", "\\literature\\")

# Patterns that introduce a file path written by the shell.
# Each pattern captures the target path in group 1.
WRITE_PATTERNS = [
    # POSIX redirects: > path  or  >> path  or  &> path  or  &>> path
    re.compile(r"(?:^|[\s|&;])(?:[12]?>>?|&>>?)\s*([^\s|&;<>]+)"),
    # tee path / tee -a path / tee --append path
    re.compile(r"\btee\b(?:\s+-[aA]\w*|\s+--append)?\s+([^\s|&;<>]+)"),
    # sed -i path  (in-place edit)
    re.compile(r"\bsed\b[^|;&]*?-i[^\s]*\s+(?:-e\s+\S+\s+)?([^\s|&;<>]+)"),
    # cp src dst   (last arg is destination; conservative: any token ending in .py/.ipynb anywhere)
    re.compile(r"\b(?:cp|mv|install|rsync)\b[^|;&]*"),
    # PowerShell redirects and cmdlets
    re.compile(r"\bSet-Content\b[^|;&]*?(?:-Path\s+)?['\"]?([^'\"\s|;&]+)"),
    re.compile(r"\bOut-File\b[^|;&]*?(?:-FilePath\s+)?['\"]?([^'\"\s|;&]+)"),
    re.compile(r"\bAdd-Content\b[^|;&]*?(?:-Path\s+)?['\"]?([^'\"\s|;&]+)"),
    # python -c "...open('path', 'w')..."  /  python3 -c
    re.compile(r"python[23]?\b[^|;&]*-c\b[^|;&]*open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][aw]"),
    # heredoc: cat <<EOF > path
    re.compile(r"<<[-~]?\s*\S+[^|;&]*?>>?\s*([^\s|&;<>]+)"),
]

# Generic fallback: any unquoted token ending in .py / .ipynb that's also
# preceded by something file-writey (cp/mv/install/rsync handled above) or
# appears after a redirection operator that we already matched.
COVERED_PATH_RE = re.compile(
    r"(?:^|[\s'\"=])(\S*?(?:\.py|\.ipynb))(?=[\s'\";|&]|$)"
)


def looks_like_covered_path(path: str) -> bool:
    """Return True if path is a code file inside a run dir (not docs/literature)."""
    if not path:
        return False
    norm = path.replace("\\", "/").lower()
    if not norm.endswith(COVERED_EXTENSIONS):
        return False
    if "researchpartner-runs/" not in norm:
        return False
    # Exempt: docs/ and literature/ subtrees directly under the run dir
    for exempt in ("/docs/", "/literature/"):
        if re.search(r"researchpartner-runs/[^/]+" + re.escape(exempt), norm):
            return False
    return True


def find_offending_paths(command: str) -> list[str]:
    hits: set[str] = set()
    # First, scan all .py/.ipynb tokens in the command line as candidates.
    for m in COVERED_PATH_RE.finditer(command):
        candidate = m.group(1)
        if looks_like_covered_path(candidate):
            hits.add(candidate)
    return sorted(hits)


def command_looks_writey(command: str) -> bool:
    """Return True if the command contains shell-write syntax we care about."""
    write_tokens = (
        ">", ">>", "tee", "sed", "cp", "mv", "install", "rsync",
        "Set-Content", "Out-File", "Add-Content",
        "-c open(", "open(\"", "open('", "<<",
    )
    return any(tok in command for tok in write_tokens)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Bash", "PowerShell"):
        return 0

    command = payload.get("tool_input", {}).get("command", "") or ""
    if not command:
        return 0

    offending = find_offending_paths(command)
    if not offending:
        return 0
    if not command_looks_writey(command):
        # A bare path mention (e.g. `python src/sim.py` to run it) is not a
        # write. Only block when the command has shell-write syntax.
        return 0

    if os.environ.get("RESEARCH_HARNESS_BYPASS_SRC_GATE") == "1":
        print(
            f"CROSS-TIER BYPASS: Bash write to {', '.join(offending)} allowed via "
            f"RESEARCH_HARNESS_BYPASS_SRC_GATE=1",
            file=sys.stderr,
        )
        return 0

    print(
        f"CROSS-TIER BLOCK: refused Bash command that writes to {', '.join(offending)}\n"
        f"  rule: Only spawned Implementation Agents may create or modify .py/.ipynb\n"
        f"        files inside a run directory. The Lead Agent and Graduate Students\n"
        f"        cannot use Bash (cat/echo/sed/cp/tee/python -c/Set-Content/...) to\n"
        f"        bypass the Write/Edit cross-tier hook.\n"
        f"  fix: spawn an Implementation Agent (skills/implementation-agent/SKILL.md)\n"
        f"       and let it produce the file via the Write tool.\n"
        f"  bypass: set RESEARCH_HARNESS_BYPASS_SRC_GATE=1 for an explicit one-off waiver.\n"
        f"  command: {command[:240]}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
