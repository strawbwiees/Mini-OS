"""Operating System Simulator - entry point.

Run:   python main.py          (needs:  pip install PySide6)
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from main_window import load_main_window


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    app.setApplicationName("Operating System Simulator")

    # Load every font file in ./fonts (Fredoka), then use it with fallbacks.
    fonts_dir = Path(__file__).resolve().parent / "fonts"
    for f in fonts_dir.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))
    font = QFont()
    font.setFamilies(["Fredoka", "Poppins", "Segoe UI", "Helvetica Neue", "Arial"])
    font.setPointSize(10)
    app.setFont(font)

    style_path = Path(__file__).resolve().parent / "styles.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))
    else:
        print(f"WARNING: stylesheet not found: {style_path}")

    ui_path = Path(__file__).resolve().parent / "main_window.ui"
    try:
        window = load_main_window(ui_path)
    except RuntimeError as error:
        print(f"ERROR: {error}")
        sys.exit(1)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()