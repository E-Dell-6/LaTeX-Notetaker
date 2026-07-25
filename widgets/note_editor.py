"""
note_editor.py

Modal-ish editor for a single note: a plain-text/LaTeX source pane on the
left, a live KaTeX-rendered preview on the right, and a backlinks panel
at the bottom showing which other notes reference this one.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTextEdit, QLineEdit,
    QLabel, QListWidget, QListWidgetItem, QPushButton, QWidget
)

from widgets.katex_view import KatexPreview


class NoteEditorDialog(QDialog):
    note_saved = pyqtSignal(int)          # note_id
    open_note_requested = pyqtSignal(int)  # follow a backlink / wikilink

    def __init__(self, db, note_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.note_id = note_id
        note = self.db.get_note(note_id)

        self.setWindowTitle(f"Note — {note.title}")
        self.resize(900, 560)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._render_preview)

        root = QVBoxLayout(self)

        self.title_edit = QLineEdit(note.title)
        self.title_edit.setStyleSheet("font-size: 18px; font-weight: 600; padding: 4px;")
        root.addWidget(self.title_edit)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(note.content)
        self.text_edit.setPlaceholderText(
            "Write notes here.\n"
            "Inline math: $a^2+b^2=c^2$\n"
            "Display math: $$\\int_0^1 x^2\\,dx$$\n"
            "Link another note: [[Other Note Title]]"
        )
        self.text_edit.textChanged.connect(self._debounce.start)
        splitter.addWidget(self.text_edit)

        self.preview = KatexPreview()
        splitter.addWidget(self.preview)
        splitter.setSizes([420, 480])
        root.addWidget(splitter, stretch=1)

        backlinks_box = QWidget()
        bl_layout = QVBoxLayout(backlinks_box)
        bl_layout.setContentsMargins(0, 8, 0, 0)
        bl_layout.addWidget(QLabel("Linked from (backlinks):"))
        self.backlinks_list = QListWidget()
        self.backlinks_list.setMaximumHeight(90)
        self.backlinks_list.itemDoubleClicked.connect(self._on_backlink_clicked)
        bl_layout.addWidget(self.backlinks_list)
        root.addWidget(backlinks_box)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self._render_preview()
        self._refresh_backlinks()

    def _render_preview(self):
        self.preview.set_content(self.text_edit.toPlainText())

    def _refresh_backlinks(self):
        self.backlinks_list.clear()
        for n in self.db.backlinks(self.note_id):
            item = QListWidgetItem(n.title)
            item.setData(Qt.ItemDataRole.UserRole, n.id)
            self.backlinks_list.addItem(item)
        if self.backlinks_list.count() == 0:
            self.backlinks_list.addItem("(no notes link here yet)")

    def _on_backlink_clicked(self, item: QListWidgetItem):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        if note_id is not None:
            self._save()
            self.open_note_requested.emit(note_id)

    def _save(self):
        title = self.title_edit.text().strip() or "Untitled"
        content = self.text_edit.toPlainText()
        self.db.update_note_content(self.note_id, title, content)
        self.setWindowTitle(f"Note — {title}")
        self.note_saved.emit(self.note_id)
        self._refresh_backlinks()

    def closeEvent(self, event):
        self._save()
        super().closeEvent(event)
