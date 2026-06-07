#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands that write code into a project.

The Write/Edit cross-tier hook (check_src_write_authorization.py) covers the
Write and Edit tools, but a Bash command can write a file too —
``echo ... > sim.py``, ``cat <<EOF > sim.py``, ``sed -i ... sim.py``,
``cp other.py src/sim.py``, ``python -c "open('sim.py','w')..."``,
``Set-Content`` / ``Out-File`` in PowerShell, and so on. Without this hook,
Bash would be a wide-open back door around the "only spawned Graduate Students
write research code" rule.

This hook inspects the Bash ``command`` string for patterns that look like
they could create or modify a ``.py`` or ``.ipynb`` file inside a project
(layout v3: project root marked by ``.research-harness``), excluding the exempt
top-level dirs ``docs/``, ``literature/``, ``.harness/scripts/``, ``tools/`` (same
coverage as the Write/Edit hook; ``tests/`` is research code and is covered).

Detection is intentionally conservative (false positives are blocked, not
false negatives) — when in doubt the user can set
``RESEARCH_HARNESS_BYPASS_SRC_GATE=1`` (the same bypass as the Write/Edit
hook) for an explicit one-off waiver.

Exit codes:
- 0: command does not look like a covered code write
- 2: command looks like a code write to a covered project path
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _project_root as project_root_mod  # noqa: E402

COVERED_EXTENSIONS = (".py", ".ipynb")
# Top-level project dirs that are NOT cross-tier-gated research code: docs/notes,
# literature/PDFs, and vendored harness tooling (.harness/scripts/, tools/). Test code
# under tests/ IS research code and is covered.
EXEMPT_TOP_DIRS = {"docs", "literature", "scripts", "tools", ".harness"}

# Patterns that introduce a file path written by the shell.
# Each pattern captures the target path in group 1 where a single target exists.
WRITE_PATTERNS = [
    # POSIX redirects: > path  or  >> path  or  &> path  or  &>> path
    re.compile(r"(?:^|[\s|&;])(?:[12]?>>?|&>>?)\s*([^\s|&;<>]+)"),
    # tee path / tee -a path / tee --append path
    re.compile(r"\btee\b(?:\s+-[aA]\w*|\s+--append)?\s+([^\s|&;<>]+)"),
    # sed -i ... file  (in-place edit; the file is a positional arg, so this
    # has no capture group and falls into the segment-scan branch — only -i
    # forms write a file, so plain `sed 's/x/y/' f.txt` is not matched)
    re.compile(r"\bsed\b[^|;&]*?-i[^|;&]*"),
    # cp/mv/install/rsync as a COMMAND (at a command boundary + a following
    # space), not the substring "install" inside a filename like .harness/scripts/install.py.
    # No capture group → segment-scan for a .py/.ipynb target among the args.
    re.compile(r"(?:^|[\s|&;])(?:cp|mv|install|rsync)\s[^|;&]*"),
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
    """Return True if path is research code inside a project (not an exempt dir).

    Layout v3: the project root is marked by ``.research-harness``. A path is
    covered if it ends in .py/.ipynb and resolves inside a project, outside the
    exempt top-level dirs (docs/, literature/, .harness/scripts/, tests/, tools/).
    Relative paths resolve against the current working directory.
    """
    if not path:
        return False
    if not path.replace("\\", "/").lower().endswith(COVERED_EXTENSIONS):
        return False
    try:
        resolved = Path(path).resolve()
        project = project_root_mod.find_project_root(resolved, require=True)
        rel = resolved.relative_to(project)
    except (project_root_mod.ProjectRootNotFoundError, ValueError, OSError):
        return False
    top = rel.parts[0] if rel.parts else ""
    return top not in EXEMPT_TOP_DIRS


def find_offending_paths(command: str) -> list[str]:
    """Return covered .py/.ipynb paths that a shell-write operator actually targets.

    Only paths captured by a WRITE_PATTERN count — a redirect target, a
    tee/sed/Set-Content/Out-File/Add-Content target, a ``python -c open(...)``
    target, or a heredoc redirect target. For cp/mv/install/rsync (no single
    capture) we scan .py tokens inside that command segment only. A bare
    *mention* of a .py path (in an echo string, a grep pattern, an rm/ls
    argument) is not a write and is ignored — otherwise the hook false-blocks
    the Lead's routine maintenance commands.
    """
    hits: set[str] = set()
    for pat in WRITE_PATTERNS:
        for m in pat.finditer(command):
            if m.groups():
                cand = m.group(1)
                if cand and looks_like_covered_path(cand):
                    hits.add(cand)
            else:
                # cp/mv/install/rsync: scan .py tokens within the matched segment
                for mm in COVERED_PATH_RE.finditer(m.group(0)):
                    if looks_like_covered_path(mm.group(1)):
                        hits.add(mm.group(1))
    return sorted(hits)


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

    if os.environ.get("RESEARCH_HARNESS_BYPASS_SRC_GATE") == "1":
        print(
            f"CROSS-TIER BYPASS: Bash write to {', '.join(offending)} allowed via "
            f"RESEARCH_HARNESS_BYPASS_SRC_GATE=1",
            file=sys.stderr,
        )
        return 0

    print(
        f"CROSS-TIER BLOCK: refused Bash command that writes to {', '.join(offending)}\n"
        f"  rule: Only spawned Graduate Students may create or modify research\n"
        f"        .py/.ipynb files. The Professor (Lead) cannot use Bash\n"
        f"        (cat/echo/sed/cp/tee/python -c/Set-Content/...) to bypass the\n"
        f"        Write/Edit cross-tier hook.\n"
        f"  fix: spawn a Graduate Student (skills/graduate-student/SKILL.md) and\n"
        f"       let it produce the file via the Write tool.\n"
        f"  bypass: set RESEARCH_HARNESS_BYPASS_SRC_GATE=1 for an explicit one-off waiver.\n"
        f"  command: {command[:240]}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
