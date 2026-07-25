"""
katex_view.py

Embeds a QWebEngineView that renders note content as HTML with inline/
display LaTeX handled by KaTeX's auto-render extension (loaded from CDN).

Note syntax supported:
    $...$      inline math
    $$...$$    display math
    [[Title]]  wiki-link to another note (rendered as a styled span)
    plain text -> paragraphs, blank line = new paragraph
"""

import html
import re

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}}
            ],
            throwOnError: false
        }});"></script>
<style>
    body {{
        background: #1e1f26;
        color: #e8e8ec;
        font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 15px;
        line-height: 1.55;
        padding: 18px 22px;
        margin: 0;
    }}
    p {{ margin: 0 0 0.8em 0; white-space: pre-wrap; }}
    .wikilink {{
        color: #8ab4ff;
        border-bottom: 1px dotted #8ab4ff;
        cursor: pointer;
    }}
    .katex {{ font-size: 1.05em; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def note_content_to_html(content: str) -> str:
    """Escape user text, then re-insert wiki-link spans, split into paragraphs.
    Math delimiters ($...$, $$...$$) are left untouched for KaTeX auto-render."""
    escaped = html.escape(content)
    # Restore [[ ]] which html.escape doesn't touch, wrap as spans.
    def repl(m):
        title = m.group(1)
        return f'<span class="wikilink" data-title="{html.escape(title)}">[[{html.escape(title)}]]</span>'

    escaped = WIKILINK_PATTERN.sub(repl, escaped)
    paragraphs = escaped.split("\n\n") if escaped.strip() else [""]
    return "\n".join(f"<p>{p}</p>" for p in paragraphs)


class KatexPreview(QWebEngineView):
    """Read-only live preview of a note's rendered LaTeX/markdown-ish content."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)

    def set_content(self, content: str):
        body = note_content_to_html(content)
        self.setHtml(PAGE_TEMPLATE.format(body=body), baseUrl=QUrl())
