"""Builds the main window from YOUR main_window.ui.

The .ui file supplies: the window, header, sidebar buttons, workspace area and
status bar.  A few lines of code then add the layouts the .ui leaves out and
plug the eight simulator pages (pages.py) into the workspace area.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QButtonGroup, QFrame, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from pages import ALL_PAGES
from widgets import MonitorIcon

# object names used inside main_window.ui, in the same order as pages.ALL_PAGES
BUTTON_NAMES = ["btnCpuScheduling", "btnBankers", "btnPaging", "btnPageReplacement",
                "btnSegmentation", "btnFragmentation", "btnDiskScheduling",
                "btnMultiprogramming"]
# CPU-only placeholder panels in the .ui; the real pages replace them
PLACEHOLDERS = ["pageHeadingWidget", "upperPanel_widget", "resultsWidget"]
READY = "Ready to simulate..."


def load_main_window(ui_path: Path):
    loader = QUiLoader()
    ui_file = QFile(str(ui_path))
    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open {ui_path}: {ui_file.errorString()}")
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        raise RuntimeError(f"Cannot load {ui_path}: {loader.errorString()}")

    def find(cls, name):
        found = window.findChild(cls, name)
        if found is None:
            raise RuntimeError(f"main_window.ui has no widget named '{name}'")
        return found

    central = find(QWidget, "centralwidget")
    header = find(QFrame, "headerFrame")
    body = find(QWidget, "widget")              # holds sidebar + workspace
    side = find(QWidget, "sideBarWidget")
    work = find(QWidget, "workspaceWidget")

    # The .ui sets bold on the containers; keep the text normal (QSS styles the rest).
    for w in (body, side, work):
        font = w.font()
        font.setBold(False)
        w.setFont(font)
    for w in (side, work):
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    # 1) layouts the .ui does not have: header on top, body fills the rest
    root = QVBoxLayout(central)
    root.setContentsMargins(14, 14, 14, 10)
    root.setSpacing(12)
    root.addWidget(header)
    root.addWidget(body, 1)
    if header.layout() is not None:
        header.layout().insertWidget(0, MonitorIcon())
    body.layout().setContentsMargins(0, 0, 0, 0)
    body.layout().setSpacing(14)
    body.layout().setStretchFactor(work, 1)

    # 2) sidebar: stack the buttons and make them behave like tabs
    stack = QStackedWidget()
    buttons = [find(QPushButton, n) for n in BUTTON_NAMES]
    group = QButtonGroup(window)
    group.setExclusive(True)
    side_layout = QVBoxLayout(side)
    side_layout.setContentsMargins(12, 14, 12, 14)
    side_layout.setSpacing(8)
    for i, btn in enumerate(buttons):
        btn.setCheckable(True)
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        group.addButton(btn)
        side_layout.addWidget(btn)
        btn.clicked.connect(lambda checked=False, k=i: go(k))
    side_layout.addStretch(1)

    # 3) workspace: drop the CPU-only placeholders, host the 8 pages instead
    for name in PLACEHOLDERS:
        placeholder = work.findChild(QWidget, name)
        if placeholder is not None:
            placeholder.setParent(None)
            placeholder.deleteLater()
    content = QFrame()
    content.setObjectName("contentFrame")
    QVBoxLayout(content).setContentsMargins(0, 0, 0, 0)
    content.layout().addWidget(stack)
    work_layout = QVBoxLayout(work)
    work_layout.setContentsMargins(0, 0, 0, 0)
    work_layout.addWidget(content)

    # 4) status bar from the .ui replaces my custom footer
    window.menuBar().hide()
    bar = window.statusBar()

    def show_status(message: str, is_error: bool) -> None:
        bar.setStyleSheet("color: #B3365A;" if is_error else "")
        bar.showMessage(message)

    pages = []
    for cls in ALL_PAGES:
        page = cls()
        page.status.connect(show_status)
        stack.addWidget(page)
        pages.append(page)

    def go(index: int) -> None:
        stack.setCurrentIndex(index)
        buttons[index].setChecked(True)
        show_status(READY, False)

    window._pages, window._group, window._stack = pages, group, stack   # keep alive
    if window.windowTitle() in ("", "MainWindow"):
        window.setWindowTitle("Operating System Simulator")
    window.setMinimumSize(980, 660)
    window.resize(max(window.width(), 1100), max(window.height(), 800))
    go(0)
    return window