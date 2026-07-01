import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


_CACHE_ROOT = Path.home() / ".cache" / "mermaid-extract"


def _load_all_groups(current_stem: str) -> list[tuple[str, list[str]]]:
    """Return (stem, [diagram_content, ...]) for every cached stem, current first."""
    if not _CACHE_ROOT.exists():
        return []

    stems = sorted(
        (d for d in _CACHE_ROOT.iterdir() if d.is_dir()),
        key=lambda d: (d.name != current_stem, d.name),
    )
    groups = []
    for stem_dir in stems:
        mmds = sorted(stem_dir.glob("*.mmd"))
        diagrams = [f.read_text(encoding="utf-8") for f in mmds]
        if diagrams:
            groups.append((stem_dir.name, diagrams))
    return groups


def _diagram_card(content: str) -> str:
    # Strip the %% comment header before rendering so mermaid gets clean input.
    lines = content.splitlines()
    body = "\n".join(l for l in lines if not l.startswith("%%")).strip()
    source = next((l[3:].strip() for l in lines if l.startswith("%%")), "")
    subtitle = f'<p class="source">{source}</p>' if source else ""
    return f'<div class="card">{subtitle}<pre class="mermaid">{body}</pre></div>'


def generate_html(current_stem: str) -> str:
    groups = _load_all_groups(current_stem)

    nav_items = "\n".join(
        f'<a href="#{stem}" class="nav-item{" nav-current" if stem == current_stem else ""}">'
        f'<span class="nav-label" title="{stem}">{stem}</span>'
        f'<span class="badge">{len(diags)}</span></a>'
        for stem, diags in groups
    )

    sections = []
    for stem, diags in groups:
        cards = "\n".join(_diagram_card(d) for d in diags)
        sections.append(
            f'<section id="{stem}">'
            f'<h2 class="section-title{" section-current" if stem == current_stem else ""}">{stem}</h2>'
            f"{cards}</section>"
        )
    content = "\n".join(sections)

    total = sum(len(d) for _, d in groups)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Mermaid Diagrams</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: sans-serif; background: #f0f2f5; display: flex; height: 100vh; overflow: hidden; }}

    /* Sidebar */
    nav {{
      width: 220px;
      flex-shrink: 0;
      background: #1e1e2e;
      color: #cdd6f4;
      display: flex;
      flex-direction: column;
      padding: 1rem 0;
      overflow-y: auto;
    }}
    nav h1 {{
      font-size: .85rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: #6c7086;
      padding: .5rem 1rem 1rem;
    }}
    .nav-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: .5rem;
      padding: .5rem 1rem;
      color: #cdd6f4;
      text-decoration: none;
      font-size: .875rem;
      border-left: 3px solid transparent;
      transition: background .15s;
    }}
    .nav-item:hover {{ background: #313244; }}
    .nav-item.nav-current {{ border-left-color: #cba6f7; background: #2a2a3e; color: #cba6f7; font-weight: 600; }}
    .nav-label {{ flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .badge {{
      font-size: .7rem;
      background: #313244;
      border-radius: 999px;
      padding: .1rem .45rem;
      color: #a6adc8;
    }}

    /* Main content */
    main {{
      flex: 1;
      overflow-y: auto;
      padding: 2rem;
    }}
    .page-header {{ margin-bottom: 1.5rem; }}
    .page-header h1 {{ font-size: 1.4rem; color: #1e1e2e; }}
    .page-header p {{ color: #6c7086; font-size: .875rem; margin-top: .25rem; }}

    section {{ margin-bottom: 2.5rem; scroll-margin-top: 1rem; }}
    .section-title {{
      font-size: 1rem;
      color: #4a4a6a;
      padding: .4rem .75rem;
      background: #e4e6f0;
      border-radius: 6px;
      margin-bottom: 1rem;
      font-weight: 600;
    }}
    .section-title.section-current {{
      background: #ede9fe;
      color: #6d28d9;
    }}
    .card {{
      background: white;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      padding: 1.5rem;
      margin-bottom: 1rem;
      overflow-x: auto;
    }}
    .source {{
      font-size: .75rem;
      color: #9094a6;
      margin-bottom: .75rem;
      font-family: monospace;
    }}
    .mermaid {{ text-align: center; }}
  </style>
</head>
<body>
  <nav>
    <h1>Sources ({len(groups)})</h1>
    {nav_items}
  </nav>
  <main>
    <div class="page-header">
      <h1>Mermaid Diagrams</h1>
      <p>{total} diagram(s) across {len(groups)} file(s)</p>
    </div>
    {content}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    // Scroll current file into view in the sidebar
    const cur = document.querySelector('.nav-itemcurrent');
    if (cur) cur.scrollIntoView({{ block: 'nearest' }});
  </script>
</body>
</html>"""


def serve(current_stem: str, port: int) -> None:
    html = generate_html(current_stem)

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    httpd = HTTPServer(("localhost", port), _Handler)
    webbrowser.open(f"http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
