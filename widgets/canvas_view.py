from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QAction
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsSimpleTextItem, QGraphicsTextItem, QMenu
)

CARD_COLOR = QColor("#2b2d3a")
CARD_BORDER = QColor("#4a4d63")
CARD_BORDER_SELECTED = QColor("#8ab4ff")
TITLE_COLOR = QColor("#f0f0f5")
SNIPPET_COLOR = QColor("#a8a8b8")

SCENE_EXTENT = 20000                            


class NoteCardItem(QGraphicsRectItem):
    def __init__(self, note, on_moved, on_double_click):
        super().__init__(0, 0, note.width, note.height)
        self.note_id = note.id
        self._on_moved = on_moved
        self._on_double_click = on_double_click

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPos(note.x, note.y)
        self.setBrush(QBrush(CARD_COLOR))
        self.setPen(QPen(CARD_BORDER, 1.5))
        self.setZValue(1)

        self.title_item = QGraphicsSimpleTextItem(self)
        self.title_item.setPos(10, 8)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.title_item.setFont(font)
        self.title_item.setBrush(QBrush(TITLE_COLOR))

        self.snippet_item = QGraphicsTextItem(self)
        self.snippet_item.setPos(10, 32)
        self.snippet_item.setDefaultTextColor(SNIPPET_COLOR)
        self.snippet_item.setTextWidth(note.width - 20)

        self.set_note_data(note)

    def set_note_data(self, note):
        self.title_item.setText(self._elide(note.title, 26))
        snippet = note.content.strip().replace("\n", " ")
        if len(snippet) > 110:
            snippet = snippet[:110] + "…"
        self.snippet_item.setPlainText(snippet)

    @staticmethod
    def _elide(text, max_len):
        return text if len(text) <= max_len else text[: max_len - 1] + "…"

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_moved(self.note_id, self.pos().x(), self.pos().y())
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self._on_double_click(self.note_id)
        super().mouseDoubleClickEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        pen = QPen(CARD_BORDER_SELECTED if self.isSelected() else CARD_BORDER, 1.5)
        self.setPen(pen)
        super().paint(painter, option, widget)


class InfiniteCanvasView(QGraphicsView):
    note_move_requested = pyqtSignal(int, float, float)                  
    note_open_requested = pyqtSignal(int)                           
    create_note_requested = pyqtSignal(float, float)                   
    delete_note_requested = pyqtSignal(int)                         

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(-SCENE_EXTENT, -SCENE_EXTENT,
                                     SCENE_EXTENT * 2, SCENE_EXTENT * 2)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor("#17181f")))
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._items_by_note = {}
        self._panning = False
        self._pan_start = None

                      
    def load_notes(self, notes):
        self.scene.clear()
        self._items_by_note.clear()
        for note in notes:
            self._add_card(note)

    def _add_card(self, note):
        card = NoteCardItem(
            note,
            on_moved=lambda nid, x, y: self.note_move_requested.emit(nid, x, y),
            on_double_click=lambda nid: self.note_open_requested.emit(nid),
        )
        self.scene.addItem(card)
        self._items_by_note[note.id] = card
        return card

    def add_or_update_card(self, note):
        if note.id in self._items_by_note:
            self._items_by_note[note.id].set_note_data(note)
        else:
            self._add_card(note)

    def remove_card(self, note_id):
        item = self._items_by_note.pop(note_id, None)
        if item is not None:
            self.scene.removeItem(item)

                           
    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, self.backgroundBrush())
        grid = 40
        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)
        pen = QPen(QColor("#22232c"))
        pen.setWidth(0)
        painter.setPen(pen)
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid

                      
    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.itemAt(event.pos())
        menu = QMenu(self)

        if item is not None:
            card = item if isinstance(item, NoteCardItem) else item.parentItem()
            if isinstance(card, NoteCardItem):
                open_action = QAction("Open note", self)
                open_action.triggered.connect(lambda: self.note_open_requested.emit(card.note_id))
                menu.addAction(open_action)
                delete_action = QAction("Delete note", self)
                delete_action.triggered.connect(lambda: self.delete_note_requested.emit(card.note_id))
                menu.addAction(delete_action)
                menu.exec(event.globalPos())
                return

        new_action = QAction("New note here", self)
        new_action.triggered.connect(
            lambda: self.create_note_requested.emit(scene_pos.x(), scene_pos.y())
        )
        menu.addAction(new_action)
        menu.exec(event.globalPos())
