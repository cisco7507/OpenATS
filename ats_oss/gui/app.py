import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def run_gui():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
