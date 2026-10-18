# -*- coding: utf-8 -*-
"""实验四：加拿大移民来源结构与时间变化的可视化表达。"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Patch, Rectangle
from matplotlib.path import Path as MplPath
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
}
AREAS = {
    "Asia": "亚洲", "Europe": "欧洲", "Northern America": "北美洲",
    "Africa": "非洲", "Latin America and the Caribbean": "拉美和加勒比",
    "Oceania": "大洋洲",
}
COLORS = {
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


def ribbon(ax, x0, x1, a0, a1, b0, b1, color):
    middle = (x0 + x1) / 2
    points = [(x0, a0), (middle, a0), (middle, b0), (x1, b0),
              (x1, b1), (middle, b1), (middle, a1), (x0, a1), (x0, a0)]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(points, codes), facecolor=color,
                           edgecolor="white", linewidth=.5, alpha=.6))


data, years = load_canada()
data["total"] = data[years].sum(axis=1)
areas = sorted(data["AreaName"].unique(),
               key=lambda area: data.loc[data["AreaName"] == area, "total"].sum(),
               reverse=True)
formatter = plt.FuncFormatter(lambda value, _: f"{abs(value):,.0f}")

# 4.1: source continent -> development category, sized by total migrants.
pivot = data.pivot_table(index="AreaName", columns="DevName", values="total",
                         aggfunc="sum", fill_value=0).reindex(areas)
destinations = ["Developing regions", "Developed regions"]
dest_labels = {"Developing regions": "发展中地区", "Developed regions": "发达地区"}
grand_total = pivot.to_numpy().sum()
left_offsets = {}
right_offsets = {key: 0.0 for key in destinations}
cursor = 0.0
for area in areas:
    left_offsets[area] = cursor
    cursor += pivot.loc[area].sum() / grand_total
right_base = {}
cursor = 0.0
for destination in destinations:
    right_base[destination] = cursor
    cursor += pivot[destination].sum() / grand_total
fig, ax = plt.subplots(figsize=(12, 7))
for area in areas:
    left_pos = left_offsets[area]
    for destination in destinations:
        share = pivot.loc[area, destination] / grand_total
        if share == 0:
            continue
        right_pos = right_base[destination] + right_offsets[destination]
        ribbon(ax, .15, .85, left_pos, left_pos + share,
               right_pos, right_pos + share, COLORS[area])
        left_pos += share
        right_offsets[destination] += share
for area in areas:
    amount = pivot.loc[area].sum()
    bottom = left_offsets[area]
    height = amount / grand_total
    ax.add_patch(Rectangle((.12, bottom), .03, height,
                           facecolor=COLORS[area], edgecolor="white"))
    ax.text(.11, bottom + height / 2, f"{AREAS[area]}  {amount/grand_total:.1%}",
            ha="right", va="center", fontsize=10)
for destination in destinations:
    amount = pivot[destination].sum()
    bottom = right_base[destination]
    height = amount / grand_total
    ax.add_patch(Rectangle((.85, bottom), .03, height,
                           facecolor="#486579", edgecolor="white"))
    ax.text(.89, bottom + height / 2,
            f"{dest_labels[destination]}  {amount/grand_total:.1%}",
            ha="left", va="center", fontsize=10)
ax.set(xlim=(-.18, 1.18), ylim=(0, 1),
       title="加拿大移民来源大洲到发展地区的流向（1980-2013 累计）")
ax.axis("off")
fig.tight_layout()
save(fig, "实验四_任务1_桑基图.png")

# 4.2: allocate exactly 100 cells using the largest-remainder method.
area_totals = data.groupby("AreaName")["total"].sum().reindex(areas)
exact = area_totals / area_totals.sum() * 100
counts = np.floor(exact).astype(int)
for area in (exact - counts).sort_values(ascending=False).index[:100 - counts.sum()]:
    counts.loc[area] += 1
cells = [area for area in areas for _ in range(counts.loc[area])]
fig, ax = plt.subplots(figsize=(10, 7))
for index, area in enumerate(cells):
    column = index % 10
    row = index // 10
    ax.add_patch(Rectangle((column, 9 - row), .94, .94,
                           facecolor=COLORS[area], edgecolor="white", linewidth=1))
ax.set(xlim=(0, 10), ylim=(0, 10), aspect="equal",
       title="加拿大移民来源大洲方格百分比图（每格约 1%）")
ax.axis("off")
ax.legend(handles=[Patch(color=COLORS[area],
                         label=f"{AREAS[area]}  {exact.loc[area]:.1f}%")
                   for area in areas], loc="center left", bbox_to_anchor=(1.02, .5),
          frameon=False)
fig.tight_layout()
save(fig, "实验四_任务2_方格百分比图.png")

# 4.3: show how the cumulative leaders changed between the first and last year.
leaders = data.nlargest(8, "total").sort_values(2013)
fig, ax = plt.subplots(figsize=(10, 6))
positions = np.arange(len(leaders))
for position, (_, row) in zip(positions, leaders.iterrows()):
    ax.plot([row[1980], row[2013]], [position, position],
            color="#aab7ba", linewidth=2, zorder=1)
ax.scatter(leaders[1980], positions, color="#d17a46", s=85, label="1980 年", zorder=2)
ax.scatter(leaders[2013], positions, color="#247ba0", s=85, label="2013 年", zorder=2)
ax.set_yticks(positions, [name(value) for value in leaders["OdName"]])
ax.set(xlabel="年度移民人数（人）", title="累计前 8 来源国：1980 与 2013 年人数变化")
ax.xaxis.set_major_formatter(formatter)
ax.legend()
ax.grid(axis="x", alpha=.2)
fig.tight_layout()
save(fig, "实验四_任务3_哑铃图.png")

# 4.4: compare annual averages because the two periods have different lengths.
early = list(range(1980, 1990))
late = list(range(2010, 2014))
early_means = data.groupby("AreaName")[early].sum().sum(axis=1).reindex(areas) / len(early)
late_means = data.groupby("AreaName")[late].sum().sum(axis=1).reindex(areas) / len(late)
positions = np.arange(len(areas))
fig, ax = plt.subplots(figsize=(11, 6))
ax.barh(positions, -early_means.to_numpy(), color="#d17a46", label="1980 年代年均")
ax.barh(positions, late_means.to_numpy(), color="#247ba0", label="2010-2013 年年均")
ax.set_yticks(positions, [AREAS[area] for area in areas])
ax.invert_yaxis()
ax.axvline(0, color="#596a70", lw=1)
ax.set(xlabel="年度移民人数（人）", title="来源大洲移民人数金字塔图：早期与末期年均对比")
ax.xaxis.set_major_formatter(formatter)
ax.legend(loc="lower right")
ax.grid(axis="x", alpha=.18)
fig.tight_layout()
save(fig, "实验四_任务4_金字塔图.png")

# 4.5: OLS trends are descriptive fits over observed years, without extrapolation.
fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
x = np.asarray(years, dtype=float)
for ax, country, color in zip(axes, ["India", "China",
                                     "United Kingdom of Great Britain and Northern Ireland"],
                              ["#247ba0", "#c95858", "#618b4a"]):
    values = data.loc[data["OdName"] == country, years].iloc[0].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x - 1980, values, deg=1)
    fitted = slope * (x - 1980) + intercept
    r2 = 1 - np.sum((values - fitted) ** 2) / np.sum((values - values.mean()) ** 2)
    ax.scatter(years, values, color=color, s=22, label="实际人数")
    ax.plot(years, fitted, color="#303e46", lw=2,
            label=f"线性回归  斜率 {slope:+,.0f} 人/年  R²={r2:.2f}")
    ax.set(ylabel="人数（人）", title=name(country))
    ax.yaxis.set_major_formatter(formatter)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=.18)
axes[-1].set_xlabel("年份")
fig.suptitle("印度、中国与英国年度移民人数及线性回归（1980-2013）", y=.995)
fig.tight_layout()
save(fig, "实验四_任务5_三国回归趋势图.png")
