# LaTeX Notes — Infinite Canvas

A desktop LaTeX note-taking app built with Python, PyQt6, and SQLite.

## Features

- **Infinite canvas** — drag notes around a pannable, zoomable board
  (middle-mouse or two-finger drag to pan, scroll wheel to zoom).
- **KaTeX-powered LaTeX rendering** — inline `$...$` and display `$$...$$`
  math rendered live in an embedded `QWebEngineView`, side-by-side with the
  raw text editor.
- **Backlink-style connections** — write `[[Another Note]]` inside a note
  to link it; the linked note is auto-created if it doesn't exist yet, and
  it will show this note under "Linked from (backlinks)".
- **Interactive graph view** — a separate tab visualizes every note as a
  node and every `[[link]]` as an edge, laid out with a small force-directed
  (spring/repulsion) algorithm. Drag nodes, double-click to open a note.
- **SQLite-backed persistence** — notes (`title`, `content`, canvas
  position/size) and their derived links are stored in `notes.db`, created
  automatically next to `main.py` on first run.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+. `PyQt6-WebEngine` pulls in Chromium, so the first
`pip install` may take a minute; the KaTeX preview also loads KaTeX's CSS/JS
from a CDN, so an internet connection is needed for math rendering (the app
itself is fully offline otherwise, since all data lives in local SQLite).

## Usage

- **Right-click** empty canvas space → "New note here".
- **Double-click** a note card to open the editor (raw text + live preview).
- Type `[[Note Title]]` anywhere in a note's content to link to another note.
  Saving auto-creates the target note if it doesn't exist and records the
  link in SQLite.
- Switch to the **Graph** tab to see the whole note network at once.
- Use the search box in the toolbar to jump straight to a note by title.

## Project structure

```
latex_notes_app/
├── main.py                 entry point
├── main_window.py          QMainWindow: toolbar, tabs, wiring
├── database.py             SQLite schema + Note dataclass + link sync
├── widgets/
│   ├── canvas_view.py       infinite canvas (QGraphicsView) + note cards
│   ├── graph_view.py        force-directed graph of notes/links
│   ├── note_editor.py       split editor: source text + KaTeX preview
│   └── katex_view.py        QWebEngineView + KaTeX HTML template
└── requirements.txt
```
