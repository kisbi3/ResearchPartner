"""Project-root resolution for the Physics Research Harness.

After the v3 refactor the project root IS the research root — there is no
`ResearchPartner-runs/<date>-<slug>/` wrapping directory. A project is
recognised by the presence of a `.research-harness` marker file (an empty
file written by `init_research_project.py`).

Resolution rules
----------------
- `find_project_root(start)` walks upward from `start` (default: cwd)
  looking for `.research-harness`. The first directory containing the
  marker is returned.
- If no marker is found, `cwd` is returned with no error so first-time
  init can run from anywhere. Callers that require a marked project
  (the gate scripts) should pass `require=True`.
- `--project <path>` on a CLI always wins: callers resolve that explicit
  path and never walk.

Multi-thread project layout (rare)::

    MyProject/
    ├── hvg-baseline/
    │   ├── .research-harness
    │   ├── docs/  src/  outputs/  ...
    └── dhvg-extension/
        ├── .research-harness
        ├── docs/  src/  outputs/  ...

Running any gate script from inside `hvg-baseline/` resolves to that
directory as the project root. From the parent `MyProject/` the walker
finds no marker (intentionally) so the user must `cd` into a thread or
pass `--project ./hvg-baseline`.
"""

from __future__ import annotations

from pathlib import Path

MARKER_NAME = ".research-harness"


class ProjectRootNotFoundError(RuntimeError):
    """Raised when a gate-check script is called outside a marked project."""


def find_project_root(start: Path | str | None = None, *, require: bool = False) -> Path:
    """Walk upward from `start` looking for the `.research-harness` marker.

    Parameters
    ----------
    start
        Directory or file to start the search from. ``None`` means cwd.
    require
        When True, raise ``ProjectRootNotFoundError`` if no marker is found.
        When False (default) the walker falls back to the original `start`
        so first-time `init_research_project.py` can run anywhere.
    """
    if start is None:
        here = Path.cwd().resolve()
    else:
        here = Path(start).resolve()
        if here.is_file():
            here = here.parent

    current = here
    while True:
        if (current / MARKER_NAME).exists():
            return current
        if current.parent == current:  # filesystem root
            break
        current = current.parent

    if require:
        raise ProjectRootNotFoundError(
            f"No `.research-harness` marker found at or above {here}. "
            "Run `python scripts/init_research_project.py` from inside "
            "your project directory, or pass `--project <path>`."
        )
    return here


def resolve_project(explicit: Path | str | None, *, require: bool = False) -> Path:
    """CLI helper: honour an explicit `--project` flag, else walk from cwd.

    When `explicit` is provided the user has told us where the project lives —
    we trust them and never enforce the marker. The `require` flag only
    applies to the cwd-walk path; that is the case where ambiguity actually
    matters (was the user inside a project tree or not?).
    """
    if explicit is not None:
        return Path(explicit).resolve()
    return find_project_root(require=require)


def create_marker(project_root: Path) -> Path:
    """Write the `.research-harness` marker at the project root."""
    marker = project_root / MARKER_NAME
    if not marker.exists():
        marker.write_text(
            "# This file marks a Physics Research Harness project root.\n"
            "# It is created by init_research_project.py and read by\n"
            "# every gate-check script to locate the project from any\n"
            "# subdirectory. Do not delete unless removing the harness.\n",
            encoding="utf-8",
        )
    return marker
