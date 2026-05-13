#!/usr/bin/env python3
"""Validate workflow map references and generated HTML."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "workflow_map.json"
HTML = ROOT / "docs" / "workflow_map.html"


def main() -> int:
    errors: list[str] = []
    if not SOURCE.exists():
        print(f"Missing {SOURCE.relative_to(ROOT)}")
        return 1

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    for map_data in data.get("maps", []):
        nodes = map_data.get("nodes", [])
        ids = [node.get("id") for node in nodes]
        duplicate_ids = sorted({node_id for node_id in ids if ids.count(node_id) > 1})
        for node_id in duplicate_ids:
            errors.append(f"{map_data.get('id')}: duplicate node id {node_id}")

        id_set = set(ids)
        for node in nodes:
            node_id = node.get("id")
            for target in node.get("edges", []):
                if target not in id_set:
                    errors.append(f"{map_data.get('id')}/{node_id}: missing edge target {target}")
            for item in node.get("responsible", []):
                path = item.get("path", "")
                if not path:
                    errors.append(f"{map_data.get('id')}/{node_id}: empty responsible path")
                    continue
                if not (ROOT / path).exists():
                    errors.append(f"{map_data.get('id')}/{node_id}: missing responsible path {path}")

    if not HTML.exists():
        errors.append("docs/workflow_map.html has not been generated")
    else:
        html_text = HTML.read_text(encoding="utf-8", errors="ignore")
        for map_data in data.get("maps", []):
            if map_data.get("title", "") not in html_text:
                errors.append(f"HTML missing map title {map_data.get('title')}")
        for required_snippet in ("file-button", "filePreview", "Open raw file"):
            if required_snippet not in html_text:
                errors.append(f"HTML missing interactive preview snippet {required_snippet}")

    if errors:
        print("Workflow link validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Workflow link validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
