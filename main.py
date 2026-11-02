import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice


def main():
    print("Starting Operating System Simulator...")

    app = QApplication(sys.argv)

    ui_path = Path(__file__).parent / "main_window.ui"
    print(f"Looking for UI file: {ui_path}")

    if not ui_path.exists():
        print("ERROR: main_window.ui was not found!")
        input("Press Enter to exit...")
        return

    ui_file = QFile(str(ui_path))

    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        print(f"ERROR opening UI: {ui_file.errorString()}")
        input("Press Enter to exit...")
        return

    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    if window is None:
        print(f"ERROR loading UI: {loader.errorString()}")
        input("Press Enter to exit...")
        return

    print("UI loaded successfully!")
    print(f"Window title: {window.windowTitle()}")

    window.show()
    window.raise_()
    window.activateWindow()

    print(f"Window visible: {window.isVisible()}")
    print("The application is running.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()