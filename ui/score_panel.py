"""评分工作区：样本导航 + 各模型打分 + 播放与音量控制。"""

import os
import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSlider, QVBoxLayout, QWidget, QGridLayout, QFrame,
)

from app.config import get_score_type
from app import storage
from app.player import get_player
from app.settings import get_settings


class ModelCard(QFrame):
    score_changed = Signal(str, float)   # (model, score)

    def __init__(self, model_name: str, parent=None):
        super().__init__(parent)
        self.model = model_name
        self.display_name = model_name
        self.setObjectName("ModelCard")
        self.setStyleSheet(
            "QFrame#ModelCard { background: #171a23; border: 1px solid #2a2f3a; "
            "border-radius: 10px; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        top = QHBoxLayout()
        self.name_label = QLabel(model_name)
        self.name_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        top.addWidget(self.name_label)
        top.addStretch(1)
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setObjectName("Primary")
        top.addWidget(self.play_btn)
        lay.addLayout(top)

        self.score_label = QLabel("未评分")
        self.score_label.setStyleSheet("color: #9ca3af;")
        lay.addWidget(self.score_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.buttons = []
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        for i in range(1, 6):
            b = QPushButton(str(i))
            b.setCheckable(True)
            b.setFixedWidth(40)
            b.setStyleSheet(
                "QPushButton { font-size: 15px; font-weight: 600; padding: 6px; }"
                "QPushButton:checked { background: #6366f1; color: white; border: none; }"
            )
            self.btn_group.addButton(b, i)
            btn_row.addWidget(b)
            self.buttons.append(b)
        lay.addLayout(btn_row)
        lay.addStretch(1)

    def set_display_name(self, name: str):
        self.display_name = name
        self.name_label.setText(name)

    def set_score(self, score):
        if score is None:
            self.btn_group.setExclusive(False)
            for b in self.buttons:
                b.setChecked(False)
            self.btn_group.setExclusive(True)
            self.score_label.setText("未评分")
        else:
            s = int(round(score))
            if 1 <= s <= 5:
                self.btn_group.button(s).setChecked(True)
            self.score_label.setText(f"当前评分：{score:g}")


class ScorePanel(QWidget):
    """评分工作区。"""

    play_requested = Signal(str)      # (audio path)
    archive_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.archive = None
        self.sample_idx = 0
        self.score_type = None
        self._cards = {}
        self._current_model = None
        self.blind = False
        self._display_order = []   # 实际模型名，按展示顺序（盲测时被洗牌）

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        # ---- 顶部：样本导航 ----
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 上一个")
        self.next_btn = QPushButton("下一个 ▶")
        self.sample_label = QLabel("—")
        self.sample_label.setAlignment(Qt.AlignCenter)
        self.sample_label.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #e5e7eb;")
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #9ca3af;")
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.count_label)
        nav.addStretch(1)
        nav.addWidget(self.sample_label)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        # ---- 参考音频条 ----
        self.ref_frame = QFrame()
        self.ref_frame.setStyleSheet(
            "QFrame { background: #171a23; border: 1px solid #2a2f3a; border-radius: 10px; }")
        ref_lay = QHBoxLayout(self.ref_frame)
        ref_lay.setContentsMargins(14, 8, 14, 8)
        self.ref_label = QLabel("参考音频：")
        self.ref_label.setStyleSheet("color: #9ca3af;")
        ref_lay.addWidget(self.ref_label)
        self.ref_play_btn = QPushButton("▶ 播放参考")
        ref_lay.addWidget(self.ref_play_btn)
        ref_lay.addStretch(1)
        self.ref_frame.setVisible(False)
        root.addWidget(self.ref_frame)

        # ---- 音量控制 ----
        vol = QHBoxLayout()
        vol_label = QLabel("🔊 音量")
        vol_label.setStyleSheet("color: #9ca3af;")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(get_settings().volume())
        self.volume_slider.setFixedWidth(180)
        self.volume_value = QLabel(f"{get_settings().volume()}%")
        self.volume_value.setFixedWidth(42)
        vol.addWidget(vol_label)
        vol.addWidget(self.volume_slider)
        vol.addWidget(self.volume_value)
        vol.addStretch(1)
        root.addLayout(vol)

        # 应用初始音量
        get_player().set_volume(get_settings().volume() / 100.0)

        # ---- 模型卡片滚动区 ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch(1)
        scroll.setWidget(self.cards_container)
        root.addWidget(scroll, 1)

        # 信号
        self.prev_btn.clicked.connect(self._prev)
        self.next_btn.clicked.connect(self._next)
        self.volume_slider.valueChanged.connect(self._on_volume)
        self.ref_play_btn.clicked.connect(self._play_ref)

    # ---------- 数据加载 ----------
    def load_archive(self, archive, blind: bool = False):
        self.archive = archive
        self.blind = blind
        self.score_type = get_score_type(archive.get("score_type", "MOS"))
        self.sample_idx = 0

        # 清理旧卡片
        for c in list(self._cards.values()):
            self.cards_layout.removeWidget(c)
            c.deleteLater()
        self._cards.clear()

        # 模型展示顺序：盲测时打乱
        models = list(archive.get("models", []))
        if blind and len(models) > 1:
            random.shuffle(models)
        self._display_order = models

        # 创建卡片
        for pos, model in enumerate(models, start=1):
            card = ModelCard(model)
            if blind and len(models) > 1:
                card.set_display_name(f"样本 {pos}")
            card.play_btn.clicked.connect(lambda _=False, m=model: self._play_model(m))
            card.score_changed.connect(self._on_score)
            # 按钮直接驱动
            for i, b in enumerate(card.buttons, start=1):
                b.clicked.connect(
                    lambda _=False, m=model, v=i: self._set_and_save(m, float(v)))
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self._cards[model] = card

        # 参考
        ref = archive.get("reference")
        if ref and archive.get("base_dir"):
            ref_dir = os.path.join(archive["base_dir"], ref)
            if os.path.isdir(ref_dir):
                self.ref_frame.setVisible(True)
                self.ref_label.setText(f"参考音频（{ref}）：")
            else:
                self.ref_frame.setVisible(False)
        else:
            self.ref_frame.setVisible(False)

        self._refresh()

    def _refresh(self):
        if not self.archive:
            return
        samples = self.archive.get("samples", [])
        n = len(samples)
        total = storage.total_count(self.archive)
        done = storage.progress_count(self.archive)

        if n == 0:
            self.sample_label.setText("（无样本）")
            self.count_label.setText("")
        else:
            self.sample_idx = max(0, min(self.sample_idx, n - 1))
            self.sample_label.setText(f"{samples[self.sample_idx]}")
            self.count_label.setText(f"{self.sample_idx + 1} / {n}")

        # 刷新每张卡片的当前分数（先按真实模型读分，再按展示顺序排布）
        if samples and self.sample_idx < n:
            s = samples[self.sample_idx]
            for model, card in self._cards.items():
                card.set_score(storage.get_rating(self.archive, s, model))
            self._reorder_cards()

        self.prev_btn.setEnabled(self.sample_idx > 0)
        self.next_btn.setEnabled(n > 0 and self.sample_idx < n - 1)

    def _reorder_cards(self):
        """按 _display_order 重新排列卡片，并处理盲测显示名。
        盲测时每个样本重新洗牌顺序，避免顺序偏置。"""
        models = list(self.archive.get("models", []))
        if self.blind and len(models) > 1:
            random.shuffle(models)
            self._display_order = models
        # 从布局中全部取出
        for card in self._cards.values():
            self.cards_layout.removeWidget(card)
        # 按新顺序插入（保留最后的 stretch）
        stretch = self.cards_layout.takeAt(self.cards_layout.count() - 1)
        for pos, model in enumerate(self._display_order, start=1):
            card = self._cards[model]
            if self.blind and len(models) > 1:
                card.set_display_name(f"样本 {pos}")
            else:
                card.set_display_name(model)
            self.cards_layout.addWidget(card)
        self.cards_layout.addItem(stretch)

    # ---------- 事件 ----------
    def _prev(self):
        if self.sample_idx > 0:
            self.sample_idx -= 1
            self._refresh()

    def _next(self):
        n = len(self.archive.get("samples", []))
        if self.sample_idx < n - 1:
            self.sample_idx += 1
            self._refresh()

    def _current_sample(self):
        samples = self.archive.get("samples", [])
        if samples and self.sample_idx < len(samples):
            return samples[self.sample_idx]
        return None

    def _model_path(self, model):
        s = self._current_sample()
        if not s:
            return None
        base = self.archive.get("base_dir")
        if not base:
            return None
        folder = os.path.join(base, model)
        # 尝试同目录下不同扩展名
        stem = os.path.splitext(s)[0]
        if os.path.isfile(os.path.join(folder, s)):
            return os.path.join(folder, s)
        for f in os.listdir(folder) if os.path.isdir(folder) else []:
            if os.path.splitext(f)[0] == stem:
                return os.path.join(folder, f)
        return None

    def _play_model(self, model):
        self._current_model = model
        path = self._model_path(model)
        if path:
            get_player().play(path)
            self.play_requested.emit(path)

    def _play_ref(self):
        ref = self.archive.get("reference")
        s = self._current_sample()
        if not ref or not s:
            return
        base = self.archive.get("base_dir")
        folder = os.path.join(base, ref)
        path = os.path.join(folder, s)
        if os.path.isfile(path):
            get_player().play(path)
            self.play_requested.emit(path)

    def _set_and_save(self, model, score):
        s = self._current_sample()
        if not s:
            return
        storage.set_rating(self.archive, s, model, score)
        self._cards[model].set_score(score)
        self.archive_changed.emit()

    def _on_score(self, model, score):
        pass  # 保留，按钮走 _set_and_save

    def _on_volume(self, v):
        self.volume_value.setText(f"{v}%")
        get_player().set_volume(v / 100.0)
        get_settings().set_volume(v)

    def current_audio_path(self):
        if self._current_model:
            return self._model_path(self._current_model)
        return None
