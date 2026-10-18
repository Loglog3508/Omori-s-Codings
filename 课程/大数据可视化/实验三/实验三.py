# -*- coding: utf-8 -*-
"""实验三：加拿大移民来源的数据模型与多角度可视化。"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Rectangle
import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from viz_common import load_canada

OUT = Path(__file__).resolve().parent / "图"
OUT.mkdir(exist_ok=True)

NAMES = {
    "India": "印度", "China": "中国",
    "United Kingdom of Great Britain and Northern Ireland": "英国",
    "Philippines": "菲律宾", "Pakistan": "巴基斯坦",
    "United States of America": "美国",
    "Iran (Islamic Republic of)": "伊朗", "Sri Lanka": "斯里兰卡",
    "Republic of Korea": "韩国", "Poland": "波兰",
    "Lebanon": "黎巴嫩", "France": "法国",
}
AREAS = {
    "Asia": "亚洲", "Europe": "欧洲", "Northern America": "北美洲",
    "Africa": "非洲", "Latin America and the Caribbean": "拉美和加勒比",
    "Oceania": "大洋洲",
}
AREA_COLORS = {
    "Asia": "#247ba0", "Europe": "#d17a46",
    "Northern America": "#618b4a", "Africa": "#9e6a9e",
    "Latin America and the Caribbean": "#c95858", "Oceania": "#8a9283",
}


def name(value):
    return NAMES.get(value, value)


def save(fig, filename):
    fig.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", filename)


def squarify(values, x, y, width, height):
    """Return rectangles whose areas follow values, preserving input order."""
    values = list(values)
    scale = width * height / sum(values)
    sizes = [value * scale for value in values]
    rectangles = []

    def worst(row, short_side):
        if not row:
            return float("inf")
        total = sum(row)
        return max(short_side ** 2 * max(row) / total ** 2,
                   total ** 2 / (short_side ** 2 * min(row)))

    def layout(row, indices, rx, ry, rw, rh):
        total = sum(row)
        if rw >= rh:
            strip = total / rh
            offset = ry
            for size, index in zip(row, indices):
                h = size / strip
                rectangles.append((index, rx, offset, strip, h))
                offset += h
            return rx + strip, ry, rw - strip, rh
        strip = total / rw
        offset = rx
        for size, index in zip(row, indices):
            w = size / strip
            rectangles.append((index, offset, ry, w, strip))
            offset += w
        return rx, ry + strip, rw, rh - strip

    row, indices = [], []
    for index, size in enumerate(sizes):
        if row and worst(row + [size], min(width, height)) > worst(row, min(width, height)):
            x, y, width, height = layout(row, indices, x, y, width, height)
            row, indices = [], []
        row.append(size)
        indices.append(index)
    if row:
        layout(row, indices, x, y, width, height)
    return sorted(rectangles)


data, years = load_canada()
data["total"] = data[years].sum(axis=1)
top5 = data.nlargest(5, "total")
top12 = data.nlargest(12, "total")
formatter = plt.FuncFormatter(lambda value, _: f"{value:,.0f}")

# 3.1: retain the actual yearly values and make outliers visible.
series = [row[years].to_numpy(dtype=float) for _, row in top5.iterrows()]
labels = [name(value) for value in top5["OdName"]]
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.boxplot(series, tick_labels=labels, patch_artist=True,
           boxprops={"facecolor": "#8bb9ca", "edgecolor": "#356981"},
           medianprops={"color": "#c95858", "linewidth": 2},
           flierprops={"marker": "o", "markersize": 4, "markerfacecolor": "#c95858"})
ax.set(title="累计前 5 来源国的年度移民人数分布（1980-2013）", ylabel="每年移民人数（人）")
ax.yaxis.set_major_formatter(formatter)
ax.grid(axis="y", alpha=.2)
fig.tight_layout()
save(fig, "实验三_任务1_箱线图.png")

fig, ax = plt.subplots(figsize=(10, 5.5))
violin = ax.violinplot(series, showmedians=True, showextrema=True)
for body in violin["bodies"]:
    body.set_facecolor("#73a9bc")
    body.set_alpha(.75)
for key in ("cmedians", "cmins", "cmaxes", "cbars"):
    violin[key].set_color("#294d5d")
ax.set_xticks(range(1, 6), labels)
ax.set(title="累计前 5 来源国的年度移民人数密度（1980-2013）", ylabel="每年移民人数（人）")
ax.yaxis.set_major_formatter(formatter)
ax.grid(axis="y", alpha=.2)
fig.tight_layout()
save(fig, "实验三_任务1_小提琴图.png")

# 3.2: annual averages make historical change visible; bubble area follows total.
early = [y for y in years if y <= 1989]
late = [y for y in years if y >= 2010]
x = top12[early].mean(axis=1).to_numpy(dtype=float)
y = top12[late].mean(axis=1).to_numpy(dtype=float)
sizes = 2300 * top12["total"].to_numpy(dtype=float) / top12["total"].max()
colors = [AREA_COLORS[a] for a in top12["AreaName"]]
fig, ax = plt.subplots(figsize=(11, 7))
ax.scatter(x, y, s=sizes, c=colors, alpha=.65, edgecolors="white", linewidths=1)
limit = max(max(x), max(y)) * 1.12
ax.plot([0, limit], [0, limit], ls="--", lw=1, color="#889399")
label_positions = {
    "Pakistan": (1400, 11000), "Iran (Islamic Republic of)": (3200, 7800),
    "Sri Lanka": (300, 3900), "Republic of Korea": (300, 6400),
    "France": (3100, 6200), "Lebanon": (3100, 3500),
    "Poland": (6100, 1600),
}
for xi, yi, label in zip(x, y, top12["OdName"]):
    if label in label_positions:
        ax.annotate(name(label), (xi, yi), xytext=label_positions[label],
                    textcoords="data", fontsize=9,
                    arrowprops={"arrowstyle": "-", "color": "#697b81", "lw": .6})
    else:
        ax.annotate(name(label), (xi, yi), xytext=(7, 7),
                    textcoords="offset points", fontsize=9)
ax.set(xlim=(0, limit), ylim=(0, limit), xlabel="1980 年代年均人数（人）",
       ylabel="2010-2013 年年均人数（人）", title="累计前 12 来源国：早晚期变化与累计规模")
ax.xaxis.set_major_formatter(formatter)
ax.yaxis.set_major_formatter(formatter)
ax.legend(handles=[Patch(color=AREA_COLORS[a], label=AREAS[a])
                   for a in top12["AreaName"].unique()], title="来源大洲", loc="lower right")
ax.grid(alpha=.15)
fig.tight_layout()
save(fig, "实验三_任务2_气泡图.png")

# Group the treemap by continent, then partition each continent among its countries.
groups = [(area, group.sort_values("total", ascending=False))
          for area, group in top12.groupby("AreaName", sort=False)]
groups.sort(key=lambda item: item[1]["total"].sum(), reverse=True)
fig, ax = plt.subplots(figsize=(12, 7))
for group_index, gx, gy, gw, gh in squarify(
        [group["total"].sum() for _, group in groups], 0, 0, 100, 60):
    area, group = groups[group_index]
    ax.add_patch(Rectangle((gx, gy), gw, gh, fill=False, edgecolor="#263b44", linewidth=2.2))
    ax.text(gx + 1, gy + gh - 1, AREAS[area], ha="left", va="top",
            fontsize=10, weight="bold", color="#122a33", zorder=5)
    inner_y = gy + 2
    inner_h = max(gh - 4, .1)
    for index, rx, ry, rw, rh in squarify(group["total"], gx + 1, inner_y,
                                         max(gw - 2, .1), inner_h):
        row = group.iloc[index]
        ax.add_patch(Rectangle((rx, ry), rw, rh, facecolor=AREA_COLORS[area],
                               alpha=.75, edgecolor="white", linewidth=1.5))
        if rw > 8 and rh > 6:
            ax.text(rx + rw / 2, ry + rh / 2,
                    f"{name(row['OdName'])}\n{row['total']/10000:.1f} 万",
                    ha="center", va="center", color="white", fontsize=9, weight="bold")
ax.set(xlim=(0, 100), ylim=(0, 60), title="累计前 12 来源国的层级矩形树状图（大洲 / 国家）")
ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout()
save(fig, "实验三_任务2_矩形树状图.png")

# 3.3: each cell represents one calendar year, with a shared scale across countries.
fig, axes = plt.subplots(5, 1, figsize=(13, 9), sharex=True)
matrix = top5[years].to_numpy(dtype=float)
norm = Normalize(vmin=0, vmax=matrix.max())
for ax, values, label in zip(axes, matrix, labels):
    ax.imshow(values[np.newaxis, :], aspect="auto", cmap="YlGnBu", norm=norm,
              extent=(years[0] - .5, years[-1] + .5, -.5, .5))
    ax.set_yticks([0], [label])
    ax.set_yticks([], minor=True)
    for year in range(1980, 2014, 10):
        ax.axvline(year - .5, color="white", lw=2)
    ax.tick_params(axis="y", length=0, pad=12)
axes[-1].set_xticks(list(range(1980, 2014, 2)))
axes[-1].tick_params(axis="x", rotation=45)
colorbar_ax = fig.add_axes([.90, .18, .018, .65])
fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="YlGnBu"), cax=colorbar_ax,
             label="年度移民人数（人）")
fig.suptitle("累计前 5 来源国年度日历热图（每格 = 1 年）", y=.98)
fig.subplots_adjust(left=.11, right=.87, top=.92, bottom=.12, hspace=.35)
save(fig, "实验三_任务3_年度日历图.png")

# 3.4: total annual inflow, then the two leading country series as bubbles.
annual = data[years].sum(axis=0).to_numpy(dtype=float)
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.scatter(years, annual, s=55, color="#247ba0")
ax.plot(years, annual, lw=1, alpha=.5, color="#247ba0")
ax.set(xlabel="年份", ylabel="总移民人数（人）", title="加拿大外来移民年度总量（1980-2013）")
ax.yaxis.set_major_formatter(formatter)
ax.grid(alpha=.2)
fig.tight_layout()
save(fig, "实验三_任务4_年度总量散点图.png")

fig, ax = plt.subplots(figsize=(11, 6))
for country, color in [("India", "#247ba0"), ("China", "#d17a46")]:
    values = data.loc[data["OdName"] == country, years].iloc[0].to_numpy(dtype=float)
    ax.scatter(years, values, s=30 + 500 * values / matrix.max(),
               color=color, alpha=.65, edgecolors="white", label=name(country))
ax.set(xlabel="年份", ylabel="年度移民人数（人）",
       title="印度与中国年度移民人数气泡图（气泡面积按人数缩放）")
ax.yaxis.set_major_formatter(formatter)
ax.legend()
ax.grid(alpha=.2)
fig.tight_layout()
save(fig, "实验三_任务4_中印年度气泡图.png")
