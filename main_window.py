from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QLineEdit, QMessageBox, QWidget,
    QVBoxLayout, QLabel
)

from database import Database
from widgets.canvas_view import InfiniteCanvasView
from widgets.graph_view import GraphView
from widgets.note_editor import NoteEditorDialog


class MainWindow(QMainWindow):
    def __init__(self, db_path: str = "notes.db"):
        super().__init__()
        self.setWindowTitle("LaTeX Notes — Infinite Canvas")
        self.resize(1200, 780)

        self.db = Database(db_path)
        self._open_editors = {}                                                      

        self.canvas = InfiniteCanvasView()
        self.graph = GraphView()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.canvas, "Canvas")
        self.tabs.addTab(self.graph, "Graph")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        self._build_toolbar()
        self._wire_canvas_signals()
        self._wire_graph_signals()

        self.reload_all()

        if not self.db.all_notes():
            self._seed_example_notes()
            self.reload_all()

                                             
    def _build_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_note_action = QAction("+ New Note", self)
        new_note_action.setShortcut(QKeySequence("Ctrl+N"))
        new_note_action.triggered.connect(lambda: self.create_note(0, 0))
        toolbar.addAction(new_note_action)

        toolbar.addSeparator()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search notes by title…  (Enter to open)")
        self.search_box.setFixedWidth(320)
        self.search_box.returnPressed.connect(self._search_and_open)
        toolbar.addWidget(self.search_box)

        toolbar.addSeparator()

        refresh_action = QAction("Refresh Graph", self)
        refresh_action.triggered.connect(self.reload_all)
        toolbar.addAction(refresh_action)

    def _wire_canvas_signals(self):
        self.canvas.note_move_requested.connect(self._on_note_moved)
        self.canvas.note_open_requested.connect(self.open_note)
        self.canvas.create_note_requested.connect(self.create_note)
        self.canvas.delete_note_requested.connect(self.delete_note)

    def _wire_graph_signals(self):
        self.graph.node_open_requested.connect(self.open_note)

    def _seed_example_notes(self):
                                                                            
                                                                            
        welcome = self.db.create_note("Welcome", "", x=-160, y=-80)
        graph = self.db.create_note("Graph Theory", "", x=220, y=40)

        self.db.update_note_content(
            welcome.id, "Welcome",
            "Welcome to your LaTeX notebook.\n\n"
            "Inline math renders like $e^{i\\pi} + 1 = 0$.\n\n"
            "Display math:\n$$\\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}$$\n\n"
            "Link to another note with double brackets, e.g. [[Graph Theory]].",
        )
        self.db.update_note_content(
            graph.id, "Graph Theory",
            "Notes on graphs.\n\nA graph $G = (V, E)$ consists of vertices and edges. "
            "See also [[Welcome]].",
        )

                                                   
    def reload_all(self):
        notes = self.db.all_notes()
        self.canvas.load_notes(notes)
        if self.tabs.currentIndex() == 1:
            self.graph.load_graph(notes, self.db.all_links())

    def _on_tab_changed(self, index):
        if index == 1:             
            self.graph.load_graph(self.db.all_notes(), self.db.all_links())

                                                    
    def create_note(self, x: float, y: float):
        note = self.db.create_note("Untitled", "", x=x, y=y)
        self.canvas.add_or_update_card(note)
        self.open_note(note.id)

    def delete_note(self, note_id: int):
        confirm = QMessageBox.question(
            self, "Delete note", "Delete this note and its links? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_note(note_id)
            self.canvas.remove_card(note_id)
            if self.tabs.currentIndex() == 1:
                self.graph.load_graph(self.db.all_notes(), self.db.all_links())

    def open_note(self, note_id: int):
        existing = self._open_editors.get(note_id)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return

        dialog = NoteEditorDialog(self.db, note_id, parent=self)
        dialog.note_saved.connect(self._on_note_saved)
        dialog.open_note_requested.connect(self.open_note)
        dialog.finished.connect(lambda _=None: self._open_editors.pop(note_id, None))
        self._open_editors[note_id] = dialog
        dialog.show()

    def _on_note_saved(self, note_id: int):
        note = self.db.get_note(note_id)
        if note is not None:
            self.canvas.add_or_update_card(note)
                                                                               
                                                                  
        self.canvas.load_notes(self.db.all_notes())
        if self.tabs.currentIndex() == 1:
            self.graph.load_graph(self.db.all_notes(), self.db.all_links())

    def _on_note_moved(self, note_id: int, x: float, y: float):
        self.db.update_note_position(note_id, x, y)

    def _search_and_open(self):
        query = self.search_box.text().strip()
        if not query:
            return
        note = self.db.get_note_by_title(query)
        if note is None:
                                        
            matches = [n for n in self.db.all_notes() if query.lower() in n.title.lower()]
            note = matches[0] if matches else None
        if note is not None:
            self.open_note(note.id)
        else:
            QMessageBox.information(self, "Not found", f"No note matching “{query}”.")

    def closeEvent(self, event):
        for dialog in list(self._open_editors.values()):
            dialog.close()
        self.db.close()
        super().closeEvent(event)
