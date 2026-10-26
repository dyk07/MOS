"""结果图表：模型平均分柱状图 + 95% 置信区间误差棒。"""

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.font_manager as fm
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from app.statistics import build_summary

# 注册中文字体，避免图表中文显示为方框
for _font_path in (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
):
    try:
        fm.fontManager.addfont(_font_path)
    except Exception:
        pass
_fonts = {f.name for f in fm.fontManager.ttflist}
if "Noto Sans CJK SC" in _fonts:
    _CJK_FONT = "Noto Sans CJK SC"
elif "Noto Sans CJK JP" in _fonts:
    _CJK_FONT = "Noto Sans CJK JP"
elif "Noto Sans CJK TC" in _fonts:
    _CJK_FONT = "Noto Sans CJK TC"
else:
    _CJK_FONT = None

if _CJK_FONT:
    matplotlib.rcParams["font.family"] = ["sans-serif"]
    matplotlib.rcParams["font.sans-serif"] = [_CJK_FONT, "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False


def build_chart(archive) -> Figure:
    """构造包含平均分柱状图 + 误差棒的 Figure。"""
    fig = Figure(figsize=(7, 4.5), dpi=100)
    fig.patch.set_facecolor("#171a23")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#171a23")

    models = archive.get("models", [])
    summary = build_summary(archive)

    means = []
    errs = []
    labels = []
    for m in models:
        st = summary.get(m)
        if not st or st["n"] == 0:
            continue
        mean = st["mean"]
        # 误差棒长度（相对均值，双侧）。无 CI 时给 0
        half = (mean - st["lower"]) if st["lower"] is not None else 0.0
        means.append(mean)
        errs.append(half)
        labels.append(m)

    if not means:
        ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                color="#9ca3af", fontsize=14, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    x = range(len(means))
    bars = ax.bar(x, means, yerr=errs, capsize=6, color="#6366f1",
                  edgecolor="#4f46e5", error_kw=dict(ecolor="#e5e7eb",
                  elinewidth=1.5, capthick=1.5), alpha=0.92)

    # 在柱顶标注均值
    for i, (m_val, st_key) in enumerate(zip(means, labels)):
        ax.text(i, m_val + (errs[i] if errs[i] else 0.2),
                f"{m_val:.2f}", ha="center", va="bottom",
                color="#e5e7eb", fontsize=9, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right", color="#e5e7eb", fontsize=9)
    ax.set_ylabel("平均分", color="#9ca3af")
    ax.set_ylim(0, 5.6)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.tick_params(colors="#9ca3af", labelsize=9)
    ax.grid(axis="y", color="#2a2f3a", linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a2f3a")
    ax.set_title("各模型平均分与 95% 置信区间", color="#e5e7eb", fontsize=11,
                 fontweight="bold", pad=12)
    fig.tight_layout()
    return fig


class ChartCanvas(FigureCanvas):
    def __init__(self, archive=None, parent=None):
        fig = build_chart(archive) if archive else Figure(figsize=(7, 4.5), dpi=100)
        super().__init__(fig)
        self.setParent(parent)

    def refresh_chart(self, archive):
        old_fig = self.figure
        new_fig = build_chart(archive)
        self.figure = new_fig
        old_fig.clear()
        self.draw()
