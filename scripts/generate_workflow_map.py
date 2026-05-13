#!/usr/bin/env python3
"""Generate the interactive workflow map HTML from docs/workflow_map.json."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "workflow_map.json"
OUTPUT = ROOT / "docs" / "workflow_map.html"


def relative_href(path: str) -> str:
    source = ROOT / path
    return source.relative_to(OUTPUT.parent).as_posix() if source.is_relative_to(OUTPUT.parent) else Path("..", path).as_posix()


def build_html(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    title = "Physics Research Workflow Map"
    template = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>__TITLE__</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #202124;
      --muted: #5f6368;
      --line: #d2d7d3;
      --accent: #0f766e;
      --accent-2: #7c2d12;
      --focus: #0b57d0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      padding: 20px 24px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    h1 {{ margin: 0 0 6px; font-size: 24px; }}
    p {{ line-height: 1.45; }}
    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
      gap: 16px;
      padding: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }}
    button {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 10px;
      cursor: pointer;
      font: inherit;
    }}
    button:hover, button:focus-visible {{
      border-color: var(--focus);
      outline: none;
    }}
    button.active {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    .diagram-wrap {{ padding: 12px; overflow: auto; }}
    svg {{ width: 100%; min-width: 920px; height: 620px; }}
    .edge {{ stroke: #8c958f; stroke-width: 2; fill: none; marker-end: url(#arrow); }}
    .node rect {{ fill: #fff; stroke: #b9c3bd; stroke-width: 2; rx: 8; }}
    .node.active rect {{ stroke: var(--accent); stroke-width: 4; }}
    .node text {{ pointer-events: none; fill: var(--ink); }}
    .node .phase {{ fill: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .node .title {{ font-size: 15px; font-weight: 700; }}
    .node:hover rect {{ stroke: var(--focus); }}
    aside {{ padding: 16px; }}
    aside h2 {{ margin: 0 0 8px; font-size: 20px; }}
    .meta {{ color: var(--muted); font-size: 13px; margin-bottom: 14px; }}
    .section {{ margin-top: 18px; }}
    .section h3 {{ margin: 0 0 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 5px 0; }}
    a {{ color: var(--accent-2); text-decoration-thickness: 1px; text-underline-offset: 2px; }}
    .docs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .docs a {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 8px;
      text-decoration: none;
      color: var(--ink);
      background: #fbfbf8;
    }}
    .docs a:hover {{ border-color: var(--focus); }}
    footer {{
      padding: 12px 24px 20px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 900px) {{
      .shell {{ grid-template-columns: 1fr; }}
      svg {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>__TITLE__</h1>
    <p>Click a workflow node to inspect the responsible skills, docs, scripts, gates, and links. This file is generated from <a href=\"workflow_map.json\">docs/workflow_map.json</a>.</p>
  </header>
  <main class=\"shell\">
    <section class=\"panel\">
      <div class=\"tabs\" id=\"tabs\"></div>
      <div class=\"diagram-wrap\" id=\"diagram\"></div>
    </section>
    <aside class=\"panel\" id=\"details\" aria-live=\"polite\"></aside>
  </main>
  <footer>
    Related docs: <a href=\"workflow_overview.md\">workflow_overview.md</a>,
    <a href=\"workflow_diagrams.md\">workflow_diagrams.md</a>,
    <a href=\"paper_logic_diagram.md\">paper_logic_diagram.md</a>.
  </footer>
  <script>
    const DATA = __DATA__;
    let activeMap = DATA.maps[0].id;
    let activeNode = DATA.maps[0].nodes[0].id;

    function pathHref(path) {{
      if (path.startsWith('docs/')) return path.replace(/^docs\\//, '');
      return '../' + path;
    }}

    function currentMap() {{
      return DATA.maps.find(map => map.id === activeMap);
    }}

    function currentNode() {{
      const map = currentMap();
      return map.nodes.find(node => node.id === activeNode) || map.nodes[0];
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }}[char]));
    }}

    function renderTabs() {{
      const tabs = document.getElementById('tabs');
      tabs.innerHTML = '';
      DATA.maps.forEach(map => {{
        const button = document.createElement('button');
        button.textContent = map.title;
        button.className = map.id === activeMap ? 'active' : '';
        button.addEventListener('click', () => {{
          activeMap = map.id;
          activeNode = map.nodes[0].id;
          render();
        }});
        tabs.appendChild(button);
      }});
    }}

    function renderDiagram() {{
      const map = currentMap();
      const nodesById = Object.fromEntries(map.nodes.map(node => [node.id, node]));
      const edgeMarkup = map.nodes.flatMap(node =>
        (node.edges || []).map(targetId => {{
          const target = nodesById[targetId];
          if (!target) return '';
          const x1 = node.x + 180;
          const y1 = node.y + 45;
          const x2 = target.x;
          const y2 = target.y + 45;
          const mid = (x1 + x2) / 2;
          return `<path class="edge" d="M ${{x1}} ${{y1}} C ${{mid}} ${{y1}}, ${{mid}} ${{y2}}, ${{x2}} ${{y2}}" />`;
        })
      ).join('');

      const nodeMarkup = map.nodes.map(node => `
        <g class="node ${{node.id === activeNode ? 'active' : ''}}" tabindex="0" role="button" aria-label="${{escapeHtml(node.title)}}" data-node="${{escapeHtml(node.id)}}" transform="translate(${{node.x}}, ${{node.y}})">
          <rect width="190" height="92"></rect>
          <text class="phase" x="14" y="24">${{escapeHtml(node.phase)}}</text>
          <text class="title" x="14" y="48">${{escapeHtml(node.title)}}</text>
          <text x="14" y="72" font-size="12">${{escapeHtml(node.summary.slice(0, 28))}}${{node.summary.length > 28 ? '...' : ''}}</text>
        </g>
      `).join('');

      document.getElementById('diagram').innerHTML = `
        <svg viewBox="0 0 1120 620" role="img" aria-label="${{escapeHtml(map.title)}}">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#8c958f"></path>
            </marker>
          </defs>
          ${{edgeMarkup}}
          ${{nodeMarkup}}
        </svg>
      `;
      document.querySelectorAll('.node').forEach(element => {{
        const activate = () => {{
          activeNode = element.dataset.node;
          renderDiagram();
          renderDetails();
        }};
        element.addEventListener('click', activate);
        element.addEventListener('keydown', event => {{
          if (event.key === 'Enter' || event.key === ' ') {{
            event.preventDefault();
            activate();
          }}
        }});
      }});
    }}

    function renderDetails() {{
      const map = currentMap();
      const node = currentNode();
      const links = (node.responsible || []).map(item =>
        `<a href="${{pathHref(item.path)}}">${{escapeHtml(item.label)}}</a>`
      ).join('');
      const checks = (node.checks || []).map(check => `<li>${{escapeHtml(check)}}</li>`).join('');
      document.getElementById('details').innerHTML = `
        <h2>${{escapeHtml(node.title)}}</h2>
        <div class="meta">${{escapeHtml(map.title)}} / ${{escapeHtml(node.phase)}}</div>
        <p>${{escapeHtml(node.summary)}}</p>
        <div class="section">
          <h3>Responsible Files</h3>
          <div class="docs">${{links}}</div>
        </div>
        <div class="section">
          <h3>Checks</h3>
          <ul>${{checks}}</ul>
        </div>
      `;
    }}

    function render() {{
      renderTabs();
      renderDiagram();
      renderDetails();
    }}

    render();
  </script>
</body>
</html>
"""
    return (
        template.replace("__TITLE__", html.escape(title))
        .replace("__DATA__", data_json)
        .replace("{{", "{")
        .replace("}}", "}")
    )


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.write_text(build_html(data), encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
