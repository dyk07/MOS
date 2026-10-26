"""评分类型定义：MOS 与 SMOS 的评分量表和标签不同。"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class ScoreType:
    key: str
    name: str              # 显示名
    description: str
    min_score: float
    max_score: float
    step: float
    levels: List[Tuple[float, str]]  # (分数, 标签) 按分数升序

    def values(self) -> List[float]:
        """返回所有可选项，如 [1.0, 2.0, 3.0, 4.0, 5.0]。"""
        vals = []
        v = self.min_score
        while v <= self.max_score + 1e-9:
            vals.append(round(v, 2))
            v += self.step
        return vals

    def label(self, value: float) -> str:
        for v, lab in self.levels:
            if abs(v - value) < 1e-9:
                return lab
        return ""


# 预置量表
MOS = ScoreType(
    key="MOS",
    name="MOS（自然度 / 音质）",
    description="对音频整体音质、自然度的主观意见分",
    min_score=1.0,
    max_score=5.0,
    step=1.0,
    levels=[
        (1.0, "很差"),
        (2.0, "较差"),
        (3.0, "一般"),
        (4.0, "较好"),
        (5.0, "很好"),
    ],
)

SMOS = ScoreType(
    key="SMOS",
    name="SMOS（相似度）",
    description="对音频与参考音频相似度的主观意见分",
    min_score=1.0,
    max_score=5.0,
    step=1.0,
    levels=[
        (1.0, "完全不同"),
        (2.0, "较不相似"),
        (3.0, "一般"),
        (4.0, "较相似"),
        (5.0, "完全相同"),
    ],
)

SCORE_TYPES: Dict[str, ScoreType] = {t.key: t for t in (MOS, SMOS)}


def get_score_type(key: str) -> ScoreType:
    return SCORE_TYPES.get(key, MOS)
