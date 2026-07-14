#!/usr/bin/env python3
"""
mdreader.py — ein schlanker, eigenständiger Markdown-Viewer.

Zeigt eine Markdown-Datei im Browser an, im GitHub-Dark-Stil mit
"Fenster"-Codeblöcken (rot/gelb/grün + Sprachlabel + Copy-Button).
Ähnlich wie 'grip', aber ohne Abhängigkeiten (nur Python-Standardbibliothek)
und mit automatischem Live-Reload, sobald die Datei gespeichert wird.

Verwendung:
    python3 mdreader.py README.md
    python3 mdreader.py README.md --port 8080
    python3 mdreader.py README.md --no-browser
"""

import argparse
import http.server
import socket
import sys
import threading
import webbrowser
from pathlib import Path

HTML_PAGE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<link rel="stylesheet" id="hljs-dark" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<link rel="stylesheet" id="hljs-light" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" disabled>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

<style>
  :root {
    --bg: #0d1117;
    --bg-panel: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --link: #58a6ff;
    --heading: #f0f6fc;
  }
  body.light {
    --bg: #ffffff;
    --bg-panel: #f6f8fa;
    --border: #d0d7de;
    --text: #1f2328;
    --text-dim: #656d76;
    --link: #0969da;
    --heading: #1f2328;
  }
  * { box-sizing: border-box; }
  body { transition: background .15s ease, color .15s ease; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
  }
  #topbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    background: var(--bg-panel);
    border-bottom: 1px solid var(--border);
    font-size: 13px;
    color: var(--text-dim);
  }
  #topbar .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #3fb950;
    display: inline-block;
  }
  #topbar .dot.stale { background: #d29922; }
  #topbar .spacer { flex: 1; }
  #theme-toggle {
    display: flex; align-items: center; gap: 6px;
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    font-size: 13px; padding: 5px 12px; border-radius: 999px; cursor: pointer;
  }
  #theme-toggle:hover { border-color: var(--text-dim); }
  #theme-toggle svg { width: 14px; height: 14px; }
  #readme {
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 96px;
  }
  .status { color: var(--text-dim); font-style: italic; padding: 24px 0; }
  .status.error { color: #f85149; }
  #readme h1, #readme h2, #readme h3, #readme h4 {
    color: var(--heading); font-weight: 600;
    margin-top: 1.6em; margin-bottom: 0.6em; line-height: 1.3;
  }
  #readme h1 { font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: .3em; }
  #readme h2 { font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: .3em; }
  #readme h3 { font-size: 1.25em; }
  #readme p { margin: .8em 0; }
  #readme a { color: var(--link); text-decoration: none; }
  #readme a:hover { text-decoration: underline; }
  #readme ul, #readme ol { padding-left: 1.6em; }
  #readme li { margin: .3em 0; }
  #readme img { max-width: 100%; border-radius: 6px; }
  #readme blockquote {
    margin: 1em 0; padding: 0 1em; color: var(--text-dim);
    border-left: 3px solid var(--border);
  }
  #readme table { border-collapse: collapse; width: 100%; margin: 1em 0; display: block; overflow-x: auto; }
  #readme th, #readme td { border: 1px solid var(--border); padding: 6px 13px; }
  #readme th { background: var(--bg-panel); font-weight: 600; }
  #readme tr:nth-child(2n) { background: var(--bg-panel); }
  #readme hr { border: none; border-top: 1px solid var(--border); margin: 2em 0; }
  #readme :not(pre) > code {
    background: rgba(110,118,129,.4); padding: .2em .4em; border-radius: 6px;
    font-size: .9em; font-family: "JetBrains Mono","Fira Code",Consolas,monospace;
  }
  #readme .code-window {
    position: relative; background: var(--bg-panel); border: 1px solid var(--border);
    border-radius: 10px; margin: 1.2em 0; overflow: hidden;
    box-shadow: 0 8px 24px rgba(0,0,0,.35);
  }
  #readme .code-window .titlebar {
    display: flex; align-items: center; gap: 8px; padding: 10px 14px;
    background: #21262d; border-bottom: 1px solid var(--border);
  }
  #readme .code-window .dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
  #readme .code-window .dot.red { background: #ff5f56; }
  #readme .code-window .dot.yellow { background: #ffbd2e; }
  #readme .code-window .dot.green { background: #27c93f; }
  #readme .code-window .lang-label {
    margin-left: auto; font-size: 12px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: .05em;
  }
  #readme .code-window .copy-btn {
    background: transparent; border: 1px solid var(--border); color: var(--text-dim);
    font-size: 12px; padding: 3px 9px; border-radius: 6px; cursor: pointer;
  }
  #readme .code-window .copy-btn:hover { color: var(--text); border-color: var(--text-dim); }
  #readme pre { margin: 0; padding: 18px; overflow-x: auto; }
  #readme pre code.hljs {
    background: transparent; padding: 0; font-size: 14px;
    font-family: "JetBrains Mono","Fira Code",Consolas,monospace; line-height: 1.55;
  }
</style>
</head>
<body>

<div id="topbar">
  <span class="dot" id="statusdot"></span>
  <span id="statustext">__TITLE__ — live</span>
  <span class="spacer"></span>
  <button id="theme-toggle" onclick="toggleTheme()">
    <span id="theme-icon">🌙</span>
    <span id="theme-label">Dark</span>
  </button>
</div>

<div id="readme">
  <div class="status" id="initial-status">Wird geladen …</div>
</div>

<script>
  const renderer = new marked.Renderer();
  renderer.code = (code, infostring) => {
    if (code && typeof code === "object") {
      infostring = code.lang;
      code = code.text;
    }
    const language = (infostring || "text").toString().split(" ")[0];
    const validLang = hljs.getLanguage(language) ? language : "plaintext";
    const highlighted = hljs.highlight(code, { language: validLang }).value;
    const escapedForAttr = code.replace(/"/g, "&quot;");
    return `
<div class="code-window">
  <div class="titlebar">
    <span class="dot red"></span>
    <span class="dot yellow"></span>
    <span class="dot green"></span>
    <span class="lang-label">${validLang}</span>
    <button class="copy-btn" onclick="copyCode(this)" data-code="${escapedForAttr}">Copy</button>
  </div>
  <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
</div>`;
  };
  marked.setOptions({ renderer, breaks: false, gfm: true });

  function copyCode(btn) {
    const code = btn.getAttribute("data-code");
    navigator.clipboard.writeText(code).then(() => {
      const old = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = old), 1500);
    });
  }

  function applyTheme(theme) {
    const dark = theme !== "light";
    document.body.classList.toggle("light", !dark);
    document.getElementById("hljs-dark").disabled = !dark;
    document.getElementById("hljs-light").disabled = dark;
    document.getElementById("theme-icon").textContent = dark ? "🌙" : "☀️";
    document.getElementById("theme-label").textContent = dark ? "Dark" : "Light";
  }

  function toggleTheme() {
    const isLight = document.body.classList.contains("light");
    const next = isLight ? "dark" : "light";
    localStorage.setItem("mdreader-theme", next);
    applyTheme(next);
  }

  // Gespeicherte Präferenz laden, sonst System-Einstellung übernehmen
  const savedTheme = localStorage.getItem("mdreader-theme");
  const systemPrefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  applyTheme(savedTheme || (systemPrefersLight ? "light" : "dark"));

  let lastContent = null;
  const container = document.getElementById("readme");
  const dot = document.getElementById("statusdot");
  const statusText = document.getElementById("statustext");

  async function refresh() {
    try {
      const res = await fetch("/content", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      dot.classList.remove("stale");
      if (text !== lastContent) {
        lastContent = text;
        container.innerHTML = marked.parse(text);
      }
    } catch (err) {
      dot.classList.add("stale");
      statusText.textContent = "Verbindung verloren — versuche erneut …";
    }
  }

  refresh();
  setInterval(refresh, 1000);
</script>

</body>
</html>
"""


class MDHandler(http.server.BaseHTTPRequestHandler):
    md_path: Path = None  # wird beim Start gesetzt

    def log_message(self, format, *args):
        pass  # ruhige Konsole

    def do_GET(self):
        if self.path in ("/", "") or self.path.startswith("/?"):
            self._send_html()
        elif self.path.startswith("/content"):
            self._send_content()
        else:
            self.send_error(404, "Nicht gefunden")

    def _send_html(self):
        page = HTML_PAGE.replace("__TITLE__", self.md_path.name)
        encoded = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_content(self):
        try:
            text = self.md_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.send_error(404, "Markdown-Datei nicht gefunden")
            return
        encoded = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)


def find_free_port(start=6419, tries=100):
    port = start
    for _ in range(tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    raise RuntimeError("Kein freier Port gefunden")


def main():
    parser = argparse.ArgumentParser(
        description="Zeigt eine Markdown-Datei live im Browser an (GitHub-Dark-Stil)."
    )
    parser.add_argument("file", help="Pfad zur Markdown-Datei, z. B. README.md")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port (Standard: automatisch einen freien Port ab 6419 suchen)"
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Browser nicht automatisch öffnen"
    )
    args = parser.parse_args()

    md_path = Path(args.file).resolve()
    if not md_path.exists():
        print(f"Fehler: Datei nicht gefunden: {md_path}")
        sys.exit(1)

    port = args.port if args.port else find_free_port()

    MDHandler.md_path = md_path
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), MDHandler)

    url = f"http://127.0.0.1:{port}/"
    print(f"📖  {md_path.name} wird angezeigt unter {url}")
    print("    Änderungen an der Datei werden automatisch übernommen.")
    print("    Zum Beenden: Strg+C")

    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
        server.shutdown()


if __name__ == "__main__":
    main()
