import sys

from PySide6.QtWidgets import QApplication

from app.ui.main_window_v2 import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

