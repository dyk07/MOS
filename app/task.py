"""任务扫描：从模型推理文件夹中找出同名音频。"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".opus", ".wma"}


def natural_key(name: str):
    """自然排序键：file2 < file10。"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


@dataclass
class Task:
    base_dir: str
    models: List[str] = field(default_factory=list)      # 模型文件夹名
    samples: List[str] = field(default_factory=list)      # 同名音频文件名
    reference: Optional[str] = None                       # 可选参考文件夹名

    @property
    def is_valid(self) -> bool:
        return bool(self.models) and bool(self.samples)


def _audio_files(folder: str) -> List[str]:
    try:
        entries = os.listdir(folder)
    except OSError:
        return []
    files = []
    for e in entries:
        p = os.path.join(folder, e)
        if os.path.isfile(p) and os.path.splitext(e)[1].lower() in AUDIO_EXTS:
            files.append(e)
    return sorted(set(files), key=natural_key)


def scan_task(base_dir: str, reference: Optional[str] = None) -> Task:
    """扫描 base_dir 下的子文件夹，每个子文件夹视为一个模型，
    取所有模型共有的同名音频作为样本列表。"""
    base_dir = os.path.abspath(base_dir)
    if not os.path.isdir(base_dir):
        return Task(base_dir=base_dir)

    subdirs = []
    for e in sorted(os.listdir(base_dir), key=natural_key):
        p = os.path.join(base_dir, e)
        if os.path.isdir(p):
            subdirs.append(e)

    models = []
    model_files = {}
    for name in subdirs:
        files = _audio_files(os.path.join(base_dir, name))
        if files:
            models.append(name)
            model_files[name] = set(files)

    if not models:
        return Task(base_dir=base_dir)

    common = set(model_files[models[0]])
    for m in models[1:]:
        common &= model_files[m]

    samples = sorted(common, key=natural_key)

    # 校验参考文件夹
    ref = None
    if reference and os.path.isdir(os.path.join(base_dir, reference)):
        ref = reference

    return Task(base_dir=base_dir, models=models, samples=samples, reference=ref)


def find_reference_candidates(base_dir: str) -> List[str]:
    """在 base_dir 下寻找可能的参考文件夹（名字含 ref/gt/ground/clean）。"""
    if not os.path.isdir(base_dir):
        return []
    cands = []
    for e in os.listdir(base_dir):
        low = e.lower()
        if os.path.isdir(os.path.join(base_dir, e)) and any(
            k in low for k in ("ref", "gt", "ground", "clean", "truth", "orig")
        ):
            cands.append(e)
    return sorted(cands)
