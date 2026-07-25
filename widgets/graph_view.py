"""
graph_view.py

Interactive graph visualization of notes (nodes) and their [[wiki-link]]
derived connections (edges). Uses a lightweight iterative force-directed
layout (spring/repulsion) computed on the fly, no external graph library
required. Click-and-drag nodes to rearrange, double-click a node to open
that note.
"""

import math
import random

from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem,
    QGraphicsSimpleTextItem, QGraphicsLineItem
)

NODE_RADIUS = 26
NODE_COLOR = QColor("#3a3d52")
NODE_BORDER = QColor("#8ab4ff")
EDGE_COLOR = QColor("#4a4d63")
LABEL_COLOR = QColor("#e8e8ec")


class GraphNodeItem(QGraphicsEllipseItem):
    def __init__(self, note_id, title, on_double_click):
        super().__init__(-NODE_RADIUS, -NODE_RADIUS, NODE_RADIUS * 2, NODE_RADIUS * 2)
        self.note_id = note_id
        self._on_double_click = on_double_click
        self.edges = []  # list of GraphEdgeItem

        self.setBrush(QBrush(NODE_COLOR))
        self.setPen(QPen(NODE_BORDER, 2))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(2)

        self.label = QGraphicsSimpleTextItem(self._elide(title), self)
        font = QFont()
        font.setPointSize(9)
        self.label.setFont(font)
        self.label.setBrush(QBrush(LABEL_COLOR))
        lb_rect = self.label.boundingRect()
        self.label.setPos(-lb_rect.width() / 2, NODE_RADIUS + 4)

    @staticmethod
    def _elide(text, max_len=18):
        return text if len(text) <= max_len else text[: max_len - 1] + "…"

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self._on_double_click(self.note_id)
        super().mouseDoubleClickEvent(event)


class GraphEdgeItem(QGraphicsLineItem):
    def __init__(self, source: GraphNodeItem, target: GraphNodeItem):
        super().__init__()
        self.source = source
        self.target = target
        self.setPen(QPen(EDGE_COLOR, 1.5))
        self.setZValue(0)
        self.update_position()

    def update_position(self):
        self.setLine(
            self.source.pos().x(), self.source.pos().y(),
            self.target.pos().x(), self.target.pos().y(),
        )


class GraphView(QGraphicsView):
    node_open_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(-2000, -2000, 4000, 4000)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#17181f")))
        self._nodes = {}

    def load_graph(self, notes, links):
        self.scene.clear()
        self._nodes.clear()

        if not notes:
            return

        # Seed positions in a circle, then relax with a simple force layout.
        n = len(notes)
        radius = max(180, 60 * n)
        positions = {}
        for i, note in enumerate(notes):
            angle = 2 * math.pi * i / max(n, 1)
            positions[note.id] = QPointF(
                radius * math.cos(angle) + random.uniform(-10, 10),
                radius * math.sin(angle) + random.uniform(-10, 10),
            )

        positions = self._relax(positions, links, iterations=150)

        for note in notes:
            node = GraphNodeItem(note.id, note.title, on_double_click=self.node_open_requested.emit)
            node.setPos(positions[note.id])
            self.scene.addItem(node)
            self._nodes[note.id] = node

        for source_id, target_id in links:
            if source_id in self._nodes and target_id in self._nodes:
                edge = GraphEdgeItem(self._nodes[source_id], self._nodes[target_id])
                self.scene.addItem(edge)
                self._nodes[source_id].edges.append(edge)
                self._nodes[target_id].edges.append(edge)

        self._fit_view()

    def _fit_view(self):
        if self._nodes:
            self.setSceneRect(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
            self.fitInView(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80),
                            Qt.AspectRatioMode.KeepAspectRatio)

    @staticmethod
    def _relax(positions, links, iterations=150, k=140.0, repulsion=9000.0):
        """Very small Fruchterman-Reingold-style force layout."""
        ids = list(positions.keys())
        for _ in range(iterations):
            forces = {nid: QPointF(0, 0) for nid in ids}

            # Repulsion between all pairs.
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    delta = positions[a] - positions[b]
                    dist = math.hypot(delta.x(), delta.y()) or 0.01
                    force_mag = repulsion / (dist * dist)
                    fx, fy = (delta.x() / dist) * force_mag, (delta.y() / dist) * force_mag
                    forces[a] += QPointF(fx, fy)
                    forces[b] -= QPointF(fx, fy)

            # Spring attraction along edges.
            for source_id, target_id in links:
                if source_id not in positions or target_id not in positions:
                    continue
                delta = positions[source_id] - positions[target_id]
                dist = math.hypot(delta.x(), delta.y()) or 0.01
                force_mag = (dist - k) * 0.02
                fx, fy = (delta.x() / dist) * force_mag, (delta.y() / dist) * force_mag
                forces[source_id] -= QPointF(fx, fy)
                forces[target_id] += QPointF(fx, fy)

            for nid in ids:
                positions[nid] += forces[nid] * 0.15

        return positions

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
