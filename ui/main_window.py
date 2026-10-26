"""主窗口。"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QProgressBar, QTabWidget, QVBoxLayout, QWidget, QStatusBar,
)

from app import storage
from app.config import SCORE_TYPES
from app.player import get_player
from app.settings import get_settings
from app.task import scan_task, find_reference_candidates
from .score_panel import ScorePanel
from .result_panel import ResultPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频评分工具 · MOS / SMOS")
        self.resize(1080, 760)
        self.archive = None
        self.archive_path = None
        self.settings = get_settings()

        # 恢复窗口几何
        geo = self.settings.geometry()
        if geo is not None:
            self.restoreGeometry(geo)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # ---- 顶部标题与进度 ----
        head = QHBoxLayout()
        self.title_label = QLabel("音频评分工具")
        self.title_label.setObjectName("Title")
        head.addWidget(self.title_label)
        head.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        head.addWidget(self.progress)
        root.addLayout(head)

        self.subtitle = QLabel("MOS / SMOS 主观评分 · 支持多人分评与汇总")
        self.subtitle.setObjectName("Subtitle")
        root.addWidget(self.subtitle)

        # ---- 工具栏 ----
        toolbar = QHBoxLayout()
        self.btn_open = QPushButton("📂 打开推理文件夹")
        self.btn_open.setObjectName("Primary")
        self.btn_new = QPushButton("➕ 新建任务")
        self.btn_save = QPushButton("💾 保存")
        self.btn_save_as = QPushButton("另存为…")
        self.btn_merge = QPushButton("🧩 合并存档")
        self.btn_split = QPushButton("✂️ 拆分存档")
        self.btn_about = QPushButton("ℹ️ 说明")
        for b in (self.btn_open, self.btn_new, self.btn_save, self.btn_save_as,
                  self.btn_merge, self.btn_split, self.btn_about):
            toolbar.addWidget(b)
        toolbar.addSpacing(16)
        self.blind_check = QCheckBox("盲测（打乱模型顺序）")
        self.blind_check.setChecked(self.settings.blind())
        self.blind_check.setToolTip("开启后模型名会隐藏为「样本 N」，且每切换样本重新随机排序")
        toolbar.addWidget(self.blind_check)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        # ---- 选项卡 ----
        self.tabs = QTabWidget()
        self.score_panel = ScorePanel()
        self.result_panel = ResultPanel()
        self.tabs.addTab(self.score_panel, "🎧 评分")
        self.tabs.addTab(self.result_panel, "📊 结果")
        root.addWidget(self.tabs, 1)

        # ---- 状态栏 ----
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # 信号
        self.btn_open.clicked.connect(self.open_folder)
        self.btn_new.clicked.connect(self.new_task)
        self.btn_save.clicked.connect(self.save)
        self.btn_save_as.clicked.connect(self.save_as)
        self.btn_merge.clicked.connect(self.merge_dialog)
        self.btn_split.clicked.connect(self.split_dialog)
        self.btn_about.clicked.connect(self.about)
        self.score_panel.archive_changed.connect(self._on_changed)
        self.tabs.currentChanged.connect(self._on_tab)
        self.blind_check.toggled.connect(self._on_blind)

    def _on_blind(self, checked):
        self.settings.set_blind(checked)
        if self.archive:
            self.score_panel.load_archive(self.archive, blind=checked)

    # ---------- 动作 ----------
    def open_folder(self):
        start = self.settings.last_dir() or ""
        folder = QFileDialog.getExistingDirectory(self, "选择包含模型子文件夹的推理目录", start)
        if not folder:
            return
        task = scan_task(folder)
        if not task.is_valid:
            QMessageBox.warning(self, "提示", "未找到包含音频的模型子文件夹，请确认目录结构。")
            return
        self.settings.set_last_dir(folder)

        # 询问评分类型
        from PySide6.QtWidgets import QInputDialog
        keys = list(SCORE_TYPES.keys())
        default_idx = keys.index(self.settings.score_type()) if self.settings.score_type() in keys else 0
        key, ok = QInputDialog.getItem(
            self, "选择评分类型", "本任务使用哪种评分？", keys, default_idx, False)
        if not ok:
            return
        score_type = key
        self.settings.set_score_type(key)

        # 询问参考文件夹（可选）
        ref = None
        cands = find_reference_candidates(folder)
        if cands:
            cands_with_none = ["（无参考）"] + cands
            prev_ref = self.settings.reference()
            default_ref = cands_with_none.index(prev_ref) if prev_ref in cands_with_none else 0
            choice, ok2 = QInputDialog.getItem(
                self, "参考音频", "是否指定参考音频文件夹（用于 SMOS）？",
                cands_with_none, default_ref, False)
            if ok2 and choice != "（无参考）":
                ref = choice
        elif task.reference:
            ref = task.reference
        if ref:
            self.settings.set_reference(ref)

        self.archive = storage.new_archive(
            folder, task.models, task.samples, score_type, ref, "")
        self.archive_path = None
        self._load_into_ui()
        self.status.showMessage(
            f"已加载 {len(task.models)} 个模型 × {len(task.samples)} 个样本")

    def new_task(self):
        self.open_folder()

    def save(self):
        if not self.archive:
            return
        if not self.archive_path:
            self.save_as()
            return
        storage.save(self.archive_path, self.archive)
        self.status.showMessage(f"已保存到 {self.archive_path}", 3000)

    def save_as(self):
        if not self.archive:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存存档", "scores.json", "JSON 存档 (*.json)")
        if not path:
            return
        self.archive_path = path
        self.save()

    def merge_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择要合并的存档", "", "JSON 存档 (*.json)")
        if not files:
            return
        archives = []
        for f in files:
            a = storage.load(f)
            if a:
                archives.append(a)
        if not archives:
            QMessageBox.warning(self, "提示", "没有有效的存档文件。")
            return
        try:
            merged = storage.merge(archives)
        except ValueError as e:
            QMessageBox.warning(self, "提示", str(e))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存合并结果", "merged_scores.json", "JSON 存档 (*.json)")
        if not path:
            return
        storage.save(path, merged)
        self.archive = merged
        self.archive_path = path
        self._load_into_ui()
        QMessageBox.information(self, "完成", f"已合并 {len(archives)} 份存档。")

    def split_dialog(self):
        if not self.archive:
            QMessageBox.information(self, "提示", "请先打开或合并一个存档。")
            return
        folder = QFileDialog.getExistingDirectory(self, "选择拆分结果的输出目录")
        if not folder:
            return
        parts = storage.split(self.archive)
        for key, part in parts.items():
            storage.save(os.path.join(folder, f"{key}.json"), part)
        QMessageBox.information(self, "完成",
                                f"已拆分为 {len(parts)} 份存档到：\n{folder}")

    def about(self):
        QMessageBox.information(
            self, "说明",
            "音频主观评分工具\n\n"
            "· 打开一个「推理目录」，其中每个子文件夹代表一个模型，"
            "子文件夹内为同名音频。\n"
            "· 逐样本试听并打分（1–5 分）。\n"
            "· MOS 评音质/自然度，SMOS 评与参考的相似度。\n"
            "· 结果页自动计算各模型平均分与 95% 置信区间（t 分布）。\n"
            "· 支持多人分别评分后「合并存档」汇总，也可「拆分存档」分给多人。\n\n"
            "评分会实时写入存档文件，退出前记得保存。")

    def _load_into_ui(self):
        self.score_panel.load_archive(self.archive, blind=self.blind_check.isChecked())
        self.result_panel.set_archive(self.archive)
        self._update_title()
        self._update_progress()

    def _on_changed(self):
        self._update_progress()

    def _on_tab(self, idx):
        if idx == 1:
            self.result_panel.set_archive(self.archive)

    def _update_title(self):
        if self.archive:
            st = self.archive.get("score_type", "MOS")
            self.title_label.setText(f"音频评分工具 · {st}")
        else:
            self.title_label.setText("音频评分工具")

    def _update_progress(self):
        if not self.archive:
            self.progress.setValue(0)
            return
        total = storage.total_count(self.archive)
        done = storage.progress_count(self.archive)
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(done)
        self.progress.setFormat(f"{done}/{total}")

    def closeEvent(self, event):
        self.settings.set_geometry(self.saveGeometry())
        get_player().quit()
        super().closeEvent(event)
