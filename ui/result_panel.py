"""结果面板：展示每个模型的均值与 95% 置信区间。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app import storage
from app.statistics import build_summary, format_ci, format_ci_short
from ui.chart import ChartCanvas


class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.archive = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel("统计结果")
        title.setObjectName("Title")
        head.addWidget(title)
        head.addStretch(1)
        self.export_png_btn = QPushButton("导出图表")
        self.export_btn = QPushButton("导出 CSV")
        head.addWidget(self.export_png_btn)
        head.addWidget(self.export_btn)
        root.addLayout(head)

        hint = QLabel("平均分 ± 95% 置信区间（基于 t 分布）")
        hint.setObjectName("Subtitle")
        root.addWidget(hint)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table, 1)

        # 图表区
        self.chart = ChartCanvas()
        root.addWidget(self.chart, 1)

        self.export_btn.clicked.connect(self._export)
        self.export_png_btn.clicked.connect(self._export_png)

    def set_archive(self, archive):
        self.archive = archive
        self._refresh()

    def _export_png(self):
        if not self.archive:
            return
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出图表", "chart.png", "PNG 图片 (*.png)")
        if not path:
            return
        self.chart.figure.savefig(path, facecolor="#171a23", dpi=150)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "完成", f"图表已保存到：\n{path}")

    def _refresh(self):
        if not self.archive:
            return
        models = self.archive.get("models", [])
        summary = build_summary(self.archive)

        headers = ["模型", "平均分", "标准差", "样本数", "95% 置信区间", "置信区间(紧凑)"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(models))

        for r, model in enumerate(models):
            stat = summary.get(model)
            if not stat:
                cells = [model, "-", "-", "0", "-", "-"]
            else:
                cells = [
                    model,
                    f"{stat['mean']:.2f}",
                    f"{stat['std']:.2f}",
                    str(stat["n"]),
                    format_ci(stat),
                    format_ci_short(stat),
                ]
            for c, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignCenter)
                if c == 0:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(r, c, item)

        # 更新图表
        self.chart.refresh_chart(self.archive)

    def _export(self):
        if not self.archive:
            return
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV", "results.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        import csv
        models = self.archive.get("models", [])
        summary = build_summary(self.archive)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["模型", "平均分", "标准差", "样本数", "95%下限", "95%上限"])
            for m in models:
                st = summary.get(m)
                if st:
                    w.writerow([m, f"{st['mean']:.4f}", f"{st['std']:.4f}",
                                st["n"],
                                "" if st["lower"] is None else f"{st['lower']:.4f}",
                                "" if st["upper"] is None else f"{st['upper']:.4f}"])
                else:
                    w.writerow([m, "", "", "0", "", ""])
