#!/usr/bin/env python3
"""音频主观评分工具（MOS / SMOS）入口。

用法：
    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from app.player import get_player
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("音频评分工具")
    apply_theme(app)
    win = MainWindow()
    win.show()
    exit_code = app.exec()
    get_player().quit()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
