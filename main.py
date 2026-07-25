import sys
import os

                                                                         
import PyQt6.QtWebEngineWidgets              

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.db")
    window = MainWindow(db_path=db_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
