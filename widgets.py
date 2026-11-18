"""Reusable widgets for the Operating System Simulator (PySide6)."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
                           QTextOption)
from PySide6.QtWidgets import (QAbstractItemView, QFormLayout, QFrame,
                               QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QPushButton, QScrollArea, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

#palette
INK = "#30245F"
MUTED = "#6855A9"
PURPLE = "#7560CC"
LAVENDER = "#DCD2FA"
BORDER = "#D9CEFA"
OK_BG, OK_FG = "#DDF5E6", "#1F7A45"
BAD_BG, BAD_FG = "#FFE0E8", "#B3365A"
FREE_COLOR = "#F3EFFF"
IDLE_COLOR = "#E6E1F5"
OS_COLOR = "#B9B3D6"
BLOCK_COLORS = ["#C9C2F6", "#F7B8CB", "#FADC93", "#BFE7D4", "#B9D8F4",
                "#F5C9A9", "#DCC0F0", "#CFE8A9", "#F2B5E1", "#A9E3E8"]


class ColorMap:
    """Gives every label (P1, P2, ...) the same pastel colour everywhere."""

    def __init__(self, special: Optional[Dict[str, str]] = None):
        self._special = dict(special or {})
        self._map: Dict[str, str] = {}

    def get(self, key) -> str:
        if key in self._special:
            return self._special[key]
        if key not in self._map:
            self._map[key] = BLOCK_COLORS[len(self._map) % len(BLOCK_COLORS)]
        return self._map[key]


def draw_centered(painter: QPainter, rect: QRectF, text: str) -> None:
    painter.drawText(rect, text, QTextOption(Qt.AlignmentFlag.AlignCenter))


# --------------------------------------------------------------------------
# Small layout helpers
# --------------------------------------------------------------------------
class Card(QFrame):
    """A white rounded panel with a lavender title bar (like 'Process Input')."""

    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        outer.addWidget(self.title_label)
        host = QWidget()
        host.setObjectName("cardBody")
        self.body = QVBoxLayout(host)
        self.body.setContentsMargins(14, 12, 14, 14)
        self.body.setSpacing(10)
        outer.addWidget(host, 1)


def label(text: str, name: Optional[str] = None, wrap: bool = False) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    w.setWordWrap(wrap)
    return w


def section(text: str) -> QLabel:
    return label(text, "sectionLabel")


def hint(text: str) -> QLabel:
    return label(text, "hint", wrap=True)


def badge(text: str, kind: str = "info") -> QLabel:
    """kind: 'ok' (green), 'bad' (pink-red) or 'info' (lavender)."""
    w = QLabel(text)
    w.setObjectName("badge")
    w.setProperty("kind", kind)
    w.setWordWrap(True)
    return w


def form(layout, rows: Sequence[Tuple[str, QWidget]]) -> QFormLayout:
    f = QFormLayout()
    f.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
    f.setContentsMargins(0, 0, 0, 0)
    f.setVerticalSpacing(6)
    for text, widget in rows:
        f.addRow(label(text, "fieldLabel"), widget)
    layout.addLayout(f)
    return f


def button_row(*buttons: QPushButton) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    for b in buttons:
        lay.addWidget(b)
    return w


def tiles(items: Sequence[Tuple[str, str]], columns: int = 4) -> QWidget:
    """A grid of small 'statistic' tiles: [(title, value), ...]."""
    host = QWidget()
    grid = QGridLayout(host)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(10)
    for i, (title, value) in enumerate(items):
        tile = QFrame()
        tile.setObjectName("tile")
        lay = QVBoxLayout(tile)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)
        lay.addWidget(label(str(value), "tileValue"))
        lay.addWidget(label(title, "tileTitle", wrap=True))
        grid.addWidget(tile, i // columns, i % columns)
    for c in range(columns):
        grid.setColumnStretch(c, 1)
    return host


def hscroll(widget: QWidget, height: int) -> QScrollArea:
    """Wrap a wide widget so it scrolls sideways instead of being squashed."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(widget)
    area.viewport().setAutoFillBackground(False)
    area.setFixedHeight(height + 16)
    return area


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
def make_table(headers: Sequence[str], rows: Sequence[Sequence],
               colors: Optional[Sequence[Optional[str]]] = None,
               cell_colors: Optional[Dict[Tuple[int, int], str]] = None,
               highlight_last: bool = False, max_height: int = 340) -> QTableWidget:
    """Read-only results table that sizes itself to its rows."""
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(list(headers))
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setAlternatingRowColors(True)
    table.setWordWrap(True)
    hdr = table.horizontalHeader()
    hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    hdr.setFixedHeight(34)
    table.verticalHeader().setDefaultSectionSize(30)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem("" if value is None else str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            colour = (cell_colors or {}).get((r, c)) or (colors[r] if colors else None)
            if colour:
                item.setBackground(QBrush(QColor(colour)))
            if highlight_last and r == len(rows) - 1:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QBrush(QColor(LAVENDER)))
            table.setItem(r, c, item)
    table.setFixedHeight(min(34 + 30 * len(rows) + 4, max_height))
    return table


class RowTable(QWidget):
    """Editable table with an 'Add ...' button and a delete button on every row."""

    def __init__(self, headers: Sequence[str], defaults: Sequence[str],
                 prefix: Optional[str] = None, start: int = 1,
                 add_text: str = "+  Add Row", min_height: int = 190):
        super().__init__()
        self._defaults = list(defaults)
        self._prefix = prefix
        self._start = start
        self._cols = len(headers)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.table = QTableWidget(0, self._cols + 1)
        self.table.setObjectName("rowTable")
        self.table.setHorizontalHeaderLabels(list(headers) + [""])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self._cols, QHeaderView.ResizeMode.Fixed)
        hdr.setFixedHeight(36)
        self.table.setColumnWidth(self._cols, 46)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setMinimumHeight(min_height)
        lay.addWidget(self.table)
        add = QPushButton(add_text)
        add.setObjectName("addRowButton")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.clicked.connect(lambda checked=False: self.add_row())
        lay.addWidget(add, 0, Qt.AlignmentFlag.AlignLeft)

    # -- editing ------------------------------------------------------------
    def _next_name(self) -> str:
        used = {row[0].strip() for row in self.rows()}
        n = self._start
        while f"{self._prefix}{n}" in used:
            n += 1
        return f"{self._prefix}{n}"

    def add_row(self, values: Optional[Sequence] = None) -> None:
        if values is None:
            values = list(self._defaults)
            if self._prefix is not None:
                values[0] = self._next_name()
        row = self.table.rowCount()
        self.table.insertRow(row)
        for c in range(self._cols):
            self.table.setItem(row, c, QTableWidgetItem(str(values[c])))
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)
        btn = QPushButton("\u2715")
        btn.setObjectName("rowDelete")
        btn.setToolTip("Remove this row")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(30, 30)
        btn.clicked.connect(lambda checked=False, w=wrapper: self._remove(w))
        wl.addWidget(btn)
        self.table.setCellWidget(row, self._cols, wrapper)

    def _remove(self, wrapper: QWidget) -> None:
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, self._cols) is wrapper:
                self.table.removeRow(r)
                return

    def set_rows(self, rows: Sequence[Sequence]) -> None:
        self.table.setRowCount(0)
        for row in rows:
            self.add_row(row)

    def rows(self) -> List[List[str]]:
        out = []
        for r in range(self.table.rowCount()):
            out.append([(self.table.item(r, c).text() if self.table.item(r, c) else "")
                        for c in range(self._cols)])
        return out


# --------------------------------------------------------------------------
# Custom-painted charts
# --------------------------------------------------------------------------
class GanttChart(QWidget):
    """Horizontal Gantt chart: segments are (label, start, end)."""

    def __init__(self):
        super().__init__()
        self.colors = ColorMap({"IDLE": IDLE_COLOR})
        self._segs: List[Tuple[str, int, int]] = []
        self._bounds: Optional[Tuple[int, int]] = None
        self.setMinimumHeight(86)

    def set_segments(self, segments, colors: Optional[ColorMap] = None,
                     bounds: Optional[Tuple[int, int]] = None) -> None:
        self._segs = list(segments)
        self._bounds = bounds
        if colors is not None:
            self.colors = colors
        self.setMinimumWidth(max(420, 34 * len(self._segs)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._segs:
            p.setPen(QColor(MUTED))
            draw_centered(p, QRectF(self.rect()), "Nothing to show")
            return
        t0 = self._bounds[0] if self._bounds else self._segs[0][1]
        t1 = self._bounds[1] if self._bounds else self._segs[-1][2]
        span = max(t1 - t0, 1)
        left, top, bar_h = 16, 10, 44
        width = max(self.width() - 2 * left, 10)

        def x(t):
            return left + (t - t0) * width / span

        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(left, top, width, bar_h), 9, 9)
        p.setClipPath(clip)
        fm = p.fontMetrics()
        for name, s, e in self._segs:
            rect = QRectF(x(s), top, max(x(e) - x(s), 1.0), bar_h)
            p.setPen(QPen(QColor("#FFFFFF"), 2))
            p.setBrush(QBrush(QColor(self.colors.get(name))))
            p.drawRect(rect)
            if name != "IDLE" and fm.horizontalAdvance(name) + 8 <= rect.width():
                p.setPen(QColor(INK))
                draw_centered(p, rect, name)
        p.restore()

        # time axis
        p.setPen(QColor(MUTED))
        y = top + bar_h + 18
        times = [t0] + [e for _, _, e in self._segs]
        drawn_right = -1e9
        for i, t in enumerate(times):
            text = str(t)
            tw = fm.horizontalAdvance(text)
            tx = x(t) - tw / 2
            if i != len(times) - 1 and tx < drawn_right + 6:
                continue
            p.drawText(QPointF(max(tx, 2), y), text)
            drawn_right = tx + tw

    def sizeHint(self):
        return QSize(max(420, 34 * len(self._segs)), 86)


class BlockStrip(QWidget):
    """Memory map: a row of labelled blocks. Block = dict(label, caption, weight, color)."""

    MIN_W = 56

    def __init__(self):
        super().__init__()
        self._blocks: List[dict] = []
        self.setMinimumHeight(74)

    def set_blocks(self, blocks: Sequence[dict]) -> None:
        self._blocks = list(blocks)
        self.setMinimumWidth(max(420, self.MIN_W * len(self._blocks)))
        self.update()

    def _widths(self, avail: float) -> List[float]:
        weights = [max(float(b["weight"]), 0.0001) for b in self._blocks]
        total = sum(weights)
        widths = [avail * w / total for w in weights]
        small = [i for i, w in enumerate(widths) if w < self.MIN_W]
        if small and len(small) < len(widths):
            rest = [i for i in range(len(widths)) if i not in small]
            rest_total = sum(weights[i] for i in rest)
            for i in small:
                widths[i] = self.MIN_W
            for i in rest:
                widths[i] = max(self.MIN_W,
                                (avail - self.MIN_W * len(small)) * weights[i] / rest_total)
        elif small:
            widths = [avail / len(widths)] * len(widths)
        scale = sum(widths)
        if scale > avail:
            widths = [w * avail / scale for w in widths]
        return widths

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._blocks:
            return
        left, top, h = 8, 6, 62
        avail = max(self.width() - 2 * left, 10)
        widths = self._widths(avail)
        fm = p.fontMetrics()
        base = QFont(p.font())
        bold = QFont(base)
        bold.setBold(True)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(left, top, avail, h), 9, 9)
        p.setClipPath(clip)
        x = float(left)
        for blk, w in zip(self._blocks, widths):
            rect = QRectF(x, top, w, h)
            p.setPen(QPen(QColor("#FFFFFF"), 2))
            p.setBrush(QBrush(QColor(blk.get("color") or FREE_COLOR)))
            p.drawRect(rect)
            p.setPen(QColor(INK if blk.get("color") else MUTED))
            p.setFont(bold)
            title = elide(p, blk["label"], w - 8)
            draw_centered(p, QRectF(x, top + 6, w, 26), title)
            p.setFont(base)
            cap = elide(p, blk.get("caption", ""), w - 8)
            draw_centered(p, QRectF(x, top + 32, w, 24), cap)
            x += w
        p.restore()


def elide(painter: QPainter, text: str, width: float) -> str:
    return painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight,
                                            max(int(width), 8))


class PathChart(QWidget):
    """Disk-head movement: cylinders run left-to-right, time runs top-to-bottom."""

    def __init__(self):
        super().__init__()
        self._path: List[int] = []
        self._top = 1
        self.setMinimumWidth(480)

    def set_path(self, path: Sequence[int], disk_size: int) -> None:
        self._path = list(path)
        self._top = max(disk_size - 1, 1)
        self.setMinimumHeight(70 + 28 * len(self._path))
        self.update()

    def paintEvent(self, event):
        if not self._path:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, right, top, step = 30, 40, 36, 28
        width = max(self.width() - left - right, 10)
        n = len(self._path)
        fm = p.fontMetrics()

        def X(c):
            return left + c * width / self._top

        # vertical grid + cylinder labels
        for value in sorted({round(k * self._top / 10) for k in range(11)}):
            gx = X(value)
            p.setPen(QPen(QColor("#E3DAF8"), 1))
            p.drawLine(QPointF(gx, top - 8), QPointF(gx, top + step * (n - 1) + 10))
            p.setPen(QColor(MUTED))
            text = str(value)
            p.drawText(QPointF(gx - fm.horizontalAdvance(text) / 2, top - 16), text)
        # path
        p.setPen(QPen(QColor(PURPLE), 2))
        for i in range(n - 1):
            p.drawLine(QPointF(X(self._path[i]), top + i * step),
                       QPointF(X(self._path[i + 1]), top + (i + 1) * step))
        # points + labels
        for i, c in enumerate(self._path):
            cx, cy = X(c), top + i * step
            p.setPen(QPen(QColor(PURPLE), 2))
            p.setBrush(QBrush(QColor("#F7B8CB" if i else "#FADC93")))
            p.drawEllipse(QPointF(cx, cy), 6, 6)
            text = str(c)
            tw = fm.horizontalAdvance(text)
            tx = cx + 10 if cx + 10 + tw < self.width() else cx - 10 - tw
            p.setPen(QColor(INK))
            p.drawText(QPointF(tx, cy + 4), text)


class MonitorIcon(QWidget):
    """Tiny painted monitor used in the header (no image files needed)."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(66, 60)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#CFC6F7"), 2))
        p.setBrush(QColor("#EDE7FF"))
        p.drawRoundedRect(QRectF(4, 4, 58, 38), 8, 8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(PURPLE))
        screen = QRectF(10, 10, 46, 26)
        p.drawRoundedRect(screen, 5, 5)
        p.setPen(QColor("#FFFFFF"))
        font = QFont(p.font())
        font.setBold(True)
        p.setFont(font)
        draw_centered(p, screen, ">_")
        p.setPen(QPen(QColor("#CFC6F7"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(33, 43), QPointF(33, 51))
        p.drawLine(QPointF(21, 53), QPointF(45, 53))