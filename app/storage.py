"""存档管理：保存 / 加载 / 拆分 / 合并。

存档为单个 JSON 文件，结构：
{
  "version": 1,
  "score_type": "MOS" | "SMOS",
  "base_dir": "...",
  "models": [...],
  "samples": [...],
  "reference": null | "ref_folder",
  "listener": "可选标注",
  "created": "ISO 时间",
  "ratings": {
      "<sample>": {
          "<model>": 分数 | [分数, ...]
      }
  },
  "progress": {"<sample>": {"<model>": true, ...}}   // 已评标记
}
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

VERSION = 1


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_archive(base_dir: str, models: List[str], samples: List[str],
                score_type: str, reference: Optional[str] = None,
                listener: str = "") -> dict:
    return {
        "version": VERSION,
        "score_type": score_type,
        "base_dir": base_dir,
        "models": models,
        "samples": samples,
        "reference": reference,
        "listener": listener,
        "created": _now(),
        "ratings": {},
        "progress": {},
    }


def load(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (OSError, json.JSONDecodeError):
        return None


def save(path: str, archive: dict) -> None:
    archive["version"] = VERSION
    archive.setdefault("created", _now())
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def set_rating(archive: dict, sample: str, model: str, score: Optional[float]) -> None:
    """设置单个评分。score 为 None 表示清除。"""
    ratings = archive.setdefault("ratings", {})
    sample_map = ratings.setdefault(sample, {})
    if score is None:
        sample_map.pop(model, None)
        if not sample_map:
            ratings.pop(sample, None)
    else:
        sample_map[model] = float(score)

    # 同步 progress
    prog = archive.setdefault("progress", {})
    sp = prog.setdefault(sample, {})
    if score is None:
        sp.pop(model, None)
    else:
        sp[model] = True


def get_rating(archive: dict, sample: str, model: str) -> Optional[float]:
    v = archive.get("ratings", {}).get(sample, {}).get(model)
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return float(v[0]) if v else None
    return float(v)


def is_rated(archive: dict, sample: str, model: str) -> bool:
    return bool(archive.get("progress", {}).get(sample, {}).get(model))


def progress_count(archive: dict) -> int:
    n = 0
    for sp in archive.get("progress", {}).values():
        n += sum(1 for v in sp.values() if v)
    return n


def total_count(archive: dict) -> int:
    return len(archive.get("samples", [])) * len(archive.get("models", []))


def sample_model_scores(archive: dict, sample: str, model: str) -> List[float]:
    v = archive.get("ratings", {}).get(sample, {}).get(model)
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [float(x) for x in v]
    return [float(v)]


def add_score(archive: dict, sample: str, model: str, score: float) -> None:
    """累加一个评分（用于合并多人结果），形成列表。"""
    ratings = archive.setdefault("ratings", {})
    sample_map = ratings.setdefault(sample, {})
    existing = sample_map.get(model)
    if existing is None:
        sample_map[model] = [float(score)]
    elif isinstance(existing, list):
        existing.append(float(score))
    else:
        sample_map[model] = [float(existing), float(score)]
    prog = archive.setdefault("progress", {})
    prog.setdefault(sample, {})[model] = True


def merge(archives: List[dict]) -> dict:
    """合并多个存档（要求 models/samples/score_type 一致）。"""
    if not archives:
        raise ValueError("没有可合并的存档")
    base = archives[0]
    models = base.get("models", [])
    samples = base.get("samples", [])
    score_type = base.get("score_type", "MOS")
    merged = new_archive(base.get("base_dir", ""), list(models), list(samples),
                         score_type, base.get("reference"), "")
    for a in archives:
        if a.get("score_type") != score_type:
            raise ValueError("不同评分类型 (MOS/SMOS) 的存档不能合并")
        if a.get("models") != models or a.get("samples") != samples:
            raise ValueError("模型或样本集合不一致，无法合并")
        for sample, mmap in a.get("ratings", {}).items():
            for model, v in mmap.items():
                vals = v if isinstance(v, (list, tuple)) else [v]
                for x in vals:
                    add_score(merged, sample, model, float(x))
    merged["created"] = _now()
    merged["listener"] = "合并（%d 份）" % len(archives)
    return merged


def split(archive: dict) -> Dict[str, dict]:
    """将合并存档按评分来源拆分。由于单个 JSON 不记录来源，
    这里按每个评分条目独立拆成单份，返回 {id: archive}。"""
    result = {}
    models = archive.get("models", [])
    samples = archive.get("samples", [])
    score_type = archive.get("score_type", "MOS")
    idx = 0
    for sample, mmap in archive.get("ratings", {}).items():
        for model, v in mmap.items():
            vals = v if isinstance(v, (list, tuple)) else [v]
            for x in vals:
                key = f"part_{idx:03d}"
                part = new_archive(archive.get("base_dir", ""), list(models),
                                   list(samples), score_type,
                                   archive.get("reference"), key)
                add_score(part, sample, model, float(x))
                result[key] = part
                idx += 1
    if not result:
        # 空存档也返回一份空的
        result["part_000"] = new_archive(
            archive.get("base_dir", ""), list(models), list(samples),
            score_type, archive.get("reference"), "part_000")
    return result
