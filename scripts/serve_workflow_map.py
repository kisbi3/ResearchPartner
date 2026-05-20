#!/usr/bin/env python3
"""Local HTTP server for the workflow map dashboard.

Why
---
`workflow_map.html` is a static file that fetches `workflow_map.live.json`
on page load. Two problems with opening it as `file://...`:

1. Some browsers refuse to `fetch()` a sibling file from a file:// origin.
2. The dashboard has a **Refresh** button that needs to *regenerate*
   ``workflow_map.live.json`` from the on-disk diagram — that requires a
   subprocess, which JavaScript at `file://` can't trigger.

Running this server solves both: the HTML is served over `http://localhost`
(no CORS issue), and a single `POST /regenerate` endpoint runs the Python
regeneration in-process and the browser then re-fetches the JSON.

Usage
-----
    cd <project-root>
    python scripts/serve_workflow_map.py          # auto-opens browser
    python scripts/serve_workflow_map.py --port 8765 --no-open

Endpoints
---------
    GET  /                       → workflow_map.html
    GET  /workflow_map.html      → workflow_map.html
    GET  /workflow_map.live.json → freshest JSON (no cache headers)
    GET  /<other>                → static file under project root
    POST /regenerate             → rebuild live.json from diagram, return JSON status

The server binds to 127.0.0.1 only — never exposed externally.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import _layout as layout  # noqa: E402
import _project_root as project_root_mod  # noqa: E402


def _regenerate(project: Path) -> tuple[bool, str]:
    """Rebuild workflow_map.live.json by walking the project file system.

    Returns (ok, message). Failures are reported as a string so the UI can
    display them without needing a stack trace.
    """
    try:
        import sync_workflow  # noqa: PLC0415
        json_path = sync_workflow.sync(project)
    except Exception as exc:
        return False, f"sync_workflow.sync failed: {exc.__class__.__name__}: {exc}"

    # sync_workflow.sync() already calls _refresh_html() internally, which
    # replaces any stale bake-in HTML with the harness polling template.
    return True, f"live.json refreshed at {json_path}"


def make_handler(project: Path):
    """Build a SimpleHTTPRequestHandler bound to *project* as the docroot."""

    class Handler(SimpleHTTPRequestHandler):
        # Bind the docroot via the directory= kwarg (Python 3.7+).
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(project), **kwargs)

        def log_message(self, fmt, *args):  # quieter default logger
            sys.stderr.write(f"[serve_workflow_map] {fmt % args}\n")

        def _no_cache_headers(self) -> None:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

        def end_headers(self) -> None:
            # Apply no-cache to every GET. The live.json updates frequently
            # and stale browser caches are the #1 cause of "the dashboard is
            # not updating" tickets.
            self._no_cache_headers()
            super().end_headers()

        def do_GET(self) -> None:
            # Redirect bare / → workflow_map.html
            if self.path in ("/", "/index.html"):
                self.send_response(302)
                self.send_header("Location", "/workflow_map.html")
                self.end_headers()
                return
            super().do_GET()

        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/regenerate":
                self.send_error(404, "Unknown endpoint")
                return
            ok, msg = _regenerate(project)
            payload = json.dumps({"ok": ok, "message": msg}).encode("utf-8")
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project root (default: walk up from cwd to find .research-harness).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Port (default 8765).")
    parser.add_argument(
        "--no-open",
        dest="open_browser",
        action="store_false",
        help="Do not auto-open the browser.",
    )
    args = parser.parse_args(argv)

    try:
        project = project_root_mod.resolve_project(args.project, require=True)
    except project_root_mod.ProjectRootNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Ensure live.json + HTML exist; create them if not so the first GET succeeds.
    # sync() writes live.json and calls _refresh_html() which copies the harness
    # polling template when the HTML is absent or is a stale bake-in version.
    try:
        import sync_workflow  # noqa: PLC0415
        sync_workflow.sync(project)
    except Exception as exc:
        print(f"WARNING: could not bootstrap workflow map: {exc}", file=sys.stderr)

    Handler = make_handler(project)
    server = HTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/workflow_map.html"

    print(f"Serving workflow map at {url}")
    print(f"  project root: {project}")
    print("  Press Ctrl+C to stop.")

    if args.open_browser:
        # Give the server a moment to start accepting connections.
        threading.Thread(
            target=lambda: (time.sleep(0.3), webbrowser.open(url)),
            daemon=True,
        ).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
