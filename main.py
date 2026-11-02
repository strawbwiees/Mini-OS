
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice


def main():
    app = QApplication(sys.argv)

    # Get the directory containing main.py
    project_dir = Path(__file__).resolve().parent

    # Paths to your UI and stylesheet
    ui_path = project_dir / "main_window.ui"
    style_path = project_dir / "styles.qss"

    # Load the stylesheet
    if style_path.exists():
        try:
            stylesheet = style_path.read_text(encoding="utf-8")
            app.setStyleSheet(stylesheet)
            print("Stylesheet loaded successfully!")
        except OSError as error:
            print(f"Could not read stylesheet: {error}")
    else:
        print(f"WARNING: Stylesheet not found: {style_path}")

    # Check whether the UI file exists
    if not ui_path.exists():
        print(f"ERROR: UI file not found: {ui_path}")
        sys.exit(1)

    # Open the UI file
    ui_file = QFile(str(ui_path))

    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        print(f"ERROR opening UI: {ui_file.errorString()}")
        sys.exit(1)

    # Load the UI
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    if window is None:
        print(f"ERROR loading UI: {loader.errorString()}")
        sys.exit(1)

    # Display the window
    window.show()

    print("UI loaded successfully!")
    print(f"Window visible: {window.isVisible()}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
