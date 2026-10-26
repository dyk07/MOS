"""全局主题与样式表。"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#6366f1"        # 靛蓝主色
ACCENT_DARK = "#4f46e5"
BG = "#0f1117"            # 深色背景
BG_PANEL = "#171a23"
BG_HOVER = "#1f2430"
FG = "#e5e7eb"
FG_DIM = "#9ca3af"
BORDER = "#2a2f3a"
GOOD = "#10b981"
WARN = "#f59e0b"
BAD = "#ef4444"

STYLE = f"""
* {{
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background: {BG};
}}
QWidget {{
    background: transparent;
    color: {FG};
}}
QLabel#Title {{
    font-size: 20px;
    font-weight: 700;
}}
QLabel#Subtitle {{
    color: {FG_DIM};
    font-size: 12px;
}}
QPushButton {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 14px;
    color: {FG};
}}
QPushButton:hover {{
    background: {BG_HOVER};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background: {ACCENT_DARK};
}}
QPushButton:disabled {{
    color: #555;
    border-color: {BORDER};
}}
QPushButton#Primary {{
    background: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: {ACCENT_DARK};
}}
QPushButton#Danger {{
    background: transparent;
    border: 1px solid {BAD};
    color: {BAD};
}}
QPushButton#Danger:hover {{
    background: {BAD};
    color: white;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    color: {FG};
    selection-background-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: white;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::groove:vertical {{
    width: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::sub-page:vertical {{
    background: {ACCENT};
    border-radius: 3px;
}}
QSlider::handle:vertical {{
    background: white;
    height: 16px;
    margin: 0 -5px;
    border-radius: 8px;
}}
QTableWidget, QTableView {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    alternate-background-color: {BG_HOVER};
}}
QHeaderView::section {{
    background: {BG_HOVER};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px;
    font-weight: 600;
}}
QProgressBar {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    text-align: center;
    height: 18px;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 7px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: #3a4150;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {FG_DIM};
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    padding: 8px 18px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: white;
}}
QToolTip {{
    background: {BG_HOVER};
    color: {FG};
    border: 1px solid {BORDER};
}}
"""


def apply_theme(app: QApplication):
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.Base, QColor(BG_PANEL))
    pal.setColor(QPalette.Text, QColor(FG))
    pal.setColor(QPalette.WindowText, QColor(FG))
    pal.setColor(QPalette.ButtonText, QColor(FG))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    app.setPalette(pal)
