"""统计分析：计算平均分与 95% 置信区间（t 分布）。"""

from typing import Dict, List, Optional

import numpy as np
from scipy import stats


def confidence_interval(values: List[float], confidence: float = 0.95):
    """返回 (mean, std, n, lower, upper)。样本数 < 2 时置信区间为 None。"""
    if not values:
        return None
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if n > 1 else 0.0
    if n >= 2:
        se = std / np.sqrt(n)
        t = stats.t.ppf((1 + confidence) / 2.0, df=n - 1)
        lower = float(mean - t * se)
        upper = float(mean + t * se)
    else:
        lower = upper = None
    return {
        "mean": mean,
        "std": std,
        "n": n,
        "lower": lower,
        "upper": upper,
    }


def format_ci(stat: Optional[dict]) -> str:
    if not stat:
        return "-"
    if stat["lower"] is None:
        return f"{stat['mean']:.2f} (n={stat['n']})"
    return f"{stat['mean']:.2f} ± {stat['mean'] - stat['lower']:.2f}  [{stat['lower']:.2f}, {stat['upper']:.2f}]"


def format_ci_short(stat: Optional[dict]) -> str:
    if not stat:
        return "-"
    if stat["lower"] is None:
        return f"{stat['mean']:.2f}"
    return f"{stat['mean']:.2f}±{(stat['mean'] - stat['lower']):.2f}"


def collect_ratings(archive, sample: str, model: str) -> List[float]:
    """从存档中取某 (sample, model) 的全部评分（支持标量或列表）。"""
    model_map = archive.get("ratings", {}).get(sample, {})
    if model not in model_map:
        return []
    v = model_map[model]
    if isinstance(v, (list, tuple)):
        return [float(x) for x in v]
    return [float(v)]


def build_summary(archive) -> Dict[str, dict]:
    """按模型汇总：{model: stat}。"""
    models = archive.get("models", [])
    samples = archive.get("samples", [])
    summary = {}
    for model in models:
        vals = []
        for s in samples:
            vals.extend(collect_ratings(archive, s, model))
        summary[model] = confidence_interval(vals)
    return summary
