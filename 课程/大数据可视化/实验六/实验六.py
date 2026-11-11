# -*- coding: utf-8 -*-
"""实验六：可视化问题分析——图形如何"撒谎"，以及如何对照数据复查。"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch, Rectangle
import matplotlib.ticker as mticker
import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from viz_common import load_canada

OUT = Path(__file__).resolve().parent / "图"
OUT.mkdir(exist_ok=True)

NAMES = {
    "India": "印度", "China": "中国",
    "United Kingdom of Great Britain and Northern Ireland": "英国",
    "Philippines": "菲律宾", "Pakistan": "巴基斯坦", "Japan": "日本",
}
AREAS = {
    "Asia": "亚洲", "Europe": "欧洲", "Latin America and the Caribbean": "拉美和加勒比",
    "Africa": "非洲", "Northern America": "北美洲", "Oceania": "大洋洲",
}
# 沿用实验四的大洲配色，实验六任务 3 要对这 6 个颜色做色盲模拟
COLORS = {
    "Asia": "#247ba0", "Europe": "#d17a46",
    "Latin America and the Caribbean": "#c95858", "Africa": "#9e6a9e",
    "Northern America": "#618b4a", "Oceania": "#8a9283",
}
AREA_ORDER = ["Asia", "Europe", "Latin America and the Caribbean",
              "Africa", "Northern America", "Oceania"]
# Okabe & Ito (2008) 色盲友好配色
OKABE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#F0E442"]
# Viénot (1999) 红绿色盲（deuteranopia）RGB 近似矩阵，按行向量右乘
CVD = np.array([[0.625, 0.375, 0.0],
                [0.700, 0.300, 0.0],
                [0.000, 0.300, 0.7]])
RED = "#b00020"


def name(value):
    return NAMES.get(value, value)


def save(fig, filename):
    fig.savefig(OUT / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", filename)


def mark(ax, text, x=0.03, y=0.97, size=9.5):
    """在图内用红字标出问题编号。"""
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top",
            color=RED, fontsize=size, weight="bold", zorder=30,
            bbox=dict(facecolor="white", edgecolor=RED, alpha=.92,
                      boxstyle="round,pad=0.25"))


def sim(hex_color):
    """红绿色盲模拟：RGB 行向量右乘矩阵后裁剪到 [0,1]。"""
    return np.clip(np.asarray(mcolors.to_rgb(hex_color)) @ CVD, 0.0, 1.0)


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def squarify(values, x, y, width, height):
    """把 values 铺成面积成比例的矩形，返回 (索引, x, y, w, h)。"""
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
                rectangles.append((index, rx, offset, strip, size / strip))
                offset += size / strip
            return rx + strip, ry, rw - strip, rh
        strip = total / rw
        offset = rx
        for size, index in zip(row, indices):
            rectangles.append((index, offset, ry, size / strip, strip))
            offset += size / strip
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
    return rectangles


data, years = load_canada()
data["total"] = data[years].sum(axis=1)
grand = data["total"].sum()
area_sum = data.groupby("AreaName")["total"].sum().reindex(AREA_ORDER)
area_share = area_sum / grand
china = data.loc[data["OdName"] == "China", years].iloc[0].to_numpy(dtype=float)
japan = data.loc[data["OdName"] == "Japan", years].iloc[0].to_numpy(dtype=float)
annual = data[years].sum()
formatter = mticker.FuncFormatter(lambda value, _: f"{abs(value):,.0f}")

# ============ 6.1 问题图与修正对比 ============
fig, axes = plt.subplots(2, 4, figsize=(16, 7.8))

# 问题①：y 轴截断，柱高与数值不成比例
ax = axes[0, 0]
late = list(range(2004, 2014))
values = china[[y - 1980 for y in late]]
ax.bar(late, values, color="#c95858", width=.68)
ax.set_ylim(20000, 45000)
ax.set_title("问题①　中国年度移民（纵轴自 20,000 起）", fontsize=10)
ax.set_ylabel("人数（人）", fontsize=9)
ax.tick_params(labelsize=8)
ax.yaxis.set_major_formatter(formatter)
mark(ax, "① y 轴截断")
ax.text(.03, .06, "柱底不是 0：柱高只表示\n“高出 20,000 的部分”", transform=ax.transAxes,
        fontsize=8.5, color=RED, va="bottom",
        bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.5))
visual = (values.max() - 20000) / (values.min() - 20000)
real = values.max() / values.min()
print("6.1 视觉放大", f"{visual:.2f}x", "真实", f"{real:.2f}x", "倍数", f"{visual/real:.2f}")

# 修正①：从 0 起，并标真实增幅
ax = axes[1, 0]
ax.bar(late, values, color="#247ba0", width=.68)
ax.set_ylim(0, 46000)
ax.set_title("修正①　纵轴从 0 起", fontsize=10)
ax.set_ylabel("人数（人）", fontsize=9)
ax.tick_params(labelsize=8)
ax.yaxis.set_major_formatter(formatter)
peak = int(values.max())
peak_year = late[int(values.argmax())]
# 峰值标注放在柱顶正上方（垂直引线），起点右移 1 年，避免文字框越出左轴撞到 y 轴刻度
ax.annotate(f"峰值 {peak:,}（{peak_year}）", xy=(peak_year, peak), xytext=(peak_year + .85, 47800),
            ha="left", va="bottom", fontsize=8.5,
            arrowprops=dict(arrowstyle="->", color="#303e46", lw=.9))
ax.text(.03, .80, f"真实：{int(values[0]):,} → {int(values[1]):,}\n即 +{values[1]/values[0]-1:.1%}（2004→2005）",
        transform=ax.transAxes, fontsize=8.5, va="top", color="#1d4e63",
        bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.5))
ax.text(.03, .55, f"截断版把 {visual/real:.1f} 倍的视觉差\n当成真实差异", transform=ax.transAxes,
        fontsize=8.5, va="top", color="#303e46",
        bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.5))
ax.set_ylim(0, 52000)

# 问题②：194 个来源国直接画饼图
ax = axes[0, 1]
totals = data.sort_values("total", ascending=False)["total"].to_numpy(dtype=float)
ax.pie(totals, colors=plt.cm.tab20(np.linspace(0, 1, len(totals))),
       wedgeprops=dict(edgecolor="white", linewidth=.12))
ax.set_title(f"问题②　{len(totals)} 个来源国全部画成一个饼", fontsize=10)
mark(ax, "② 扇区过多 ", x=.01, y=.99, size=9)
ax.text(0, -.06, "每片平均 1.9°，最大的印度也只占 10.8%", ha="center",
        transform=ax.transAxes, fontsize=8.5, color=RED)
print("6.1 国家数", len(totals), "印度占比", f"{totals[0]/grand:.1%}")

# 修正②：top5 + 其他
ax = axes[1, 1]
top5 = data.nlargest(5, "total")
labels5 = [name(value) for value in top5["OdName"]]
vals5 = list(top5["total"].to_numpy(dtype=float)) + [grand - top5["total"].sum()]
labels5 = labels5 + [f"其他 {len(data) - 5} 国"]
colors5 = ["#247ba0", "#d17a46", "#618b4a", "#9e6a9e", "#c95858"] + ["#c9cfd2"]
ax.pie(vals5, labels=labels5, colors=colors5, autopct="%.1f%%", startangle=90,
       counterclock=False, pctdistance=.72, labeldistance=1.10,
       textprops=dict(fontsize=8.5), wedgeprops=dict(edgecolor="white", linewidth=1))
ax.set_title("修正②　Top5 + “其他”合并", fontsize=10)

# 问题③：爆炸 / 阴影等视觉特效
ax = axes[0, 2]
ax.pie(area_sum.to_numpy(dtype=float), colors=[COLORS[area] for area in AREA_ORDER],
       explode=[.12] * len(AREA_ORDER), shadow=True, startangle=90,
       counterclock=False, wedgeprops=dict(edgecolor="#404040", linewidth=.6))
ax.set_title("问题③　爆炸 + 阴影 + 粗描边", fontsize=10)
mark(ax, "③ 视觉特效夸大", x=.01, y=.99, size=9)
ax.text(0, -.08, "亚洲 51.8% 与欧洲 22.0% 的 2.35 倍差距\n被特效放大成“压倒性”印象",
        ha="center", transform=ax.transAxes, fontsize=8.5, color=RED)

# 修正③：平面水平条，按值排序并标百分比
ax = axes[1, 2]
order = area_sum.sort_values().index
positions = np.arange(len(order))
ax.barh(positions, area_sum.loc[order].to_numpy(dtype=float),
        color=[COLORS[area] for area in order], height=.66)
for position, area in zip(positions, order):
    ax.text(area_sum.loc[area] + grand * .012, position,
            f"{area_sum.loc[area]:,}（{area_share.loc[area]:.1%}）", va="center", fontsize=8)
ax.set_yticks(positions, [AREAS[area] for area in order])
ax.tick_params(axis="y", labelsize=8.5)
ax.set_xlim(0, grand * .80)
ax.xaxis.set_major_formatter(formatter)
ax.tick_params(axis="x", labelsize=7.5)
ax.set_xlabel("累计移民人数（人）", fontsize=8.5)
ax.set_title("修正③　平面水平条形图", fontsize=10)
ax.grid(axis="x", alpha=.2)

# 问题④：双 y 轴任意缩放，制造“日本反超”的假象
ax = axes[0, 3]
ax.plot(late, china[[y - 1980 for y in late]], color="#c95858", marker="o", ms=3.4, label="中国（左轴）")
ax.set_ylim(0, 46000)
ax.set_ylabel("中国：人数（人）", color="#c95858", fontsize=8.5)
ax.tick_params(axis="y", labelsize=7.5, colors="#c95858")
ax2 = ax.twinx()
ax2.plot(late, japan[[y - 1980 for y in late]], color="#247ba0", marker="s", ms=3.4, label="日本（右轴）")
ax2.set_ylim(0, 1300)
ax2.set_ylabel("日本：人数（人）", color="#247ba0", fontsize=8.5)
ax2.tick_params(axis="y", labelsize=7.5, colors="#247ba0")
ax.set_title("问题④　中日双 y 轴（右轴 0—1,300）", fontsize=10)
ax.tick_params(axis="x", labelsize=8)
ax.set_xlabel("年份", fontsize=8.5)
ax.grid(alpha=.15)
# 找出两条曲线在各自坐标轴归一化后交叉的年份
norm_cn = china[[y - 1980 for y in late]] / 46000
norm_jp = japan[[y - 1980 for y in late]] / 1300
crossings = [late[i] for i in range(1, len(late))
             if np.sign(norm_cn[i] - norm_jp[i]) != np.sign(norm_cn[i - 1] - norm_jp[i - 1])]
cross = crossings[-1] if crossings else None
mark(ax, "④ 双轴任意缩放", x=.01, y=.99, size=9)
if cross is not None:
    ax.axvline(cross, color=RED, ls="--", lw=1.1)
    ax.annotate(f"{cross} 年两线“交叉”\n读者以为日本反超", xy=(cross, 34000),
                xytext=(2004.4, 28500), fontsize=8, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=.9))
print("6.1 双轴交叉年", crossings, "中国2013", int(china[-1]), "日本2013", int(japan[-1]))

# 修正④：指数化到同一基准年，单轴可比
ax = axes[1, 3]
base = 2004
cn_idx = china[[y - 1980 for y in late]] / china[base - 1980] * 100
jp_idx = japan[[y - 1980 for y in late]] / japan[base - 1980] * 100
ax.plot(late, cn_idx, color="#c95858", marker="o", ms=3.4, label="中国")
ax.plot(late, jp_idx, color="#247ba0", marker="s", ms=3.4, label="日本")
ax.axhline(100, color="#889399", ls=":", lw=1)
ax.set_title(f"修正④　同一纵轴，指数化（{base}=100）", fontsize=10)
ax.set_xlabel("年份", fontsize=8.5)
ax.set_ylabel(f"以 {base} 年为 100", fontsize=8.5)
ax.tick_params(labelsize=7.5)
ax.legend(fontsize=8, loc="upper left")
ax.grid(alpha=.18)
ax.text(.03, .03, f"两轴不同时，{int(japan[-1])} 人的日本看起来\n和 {int(china[-1]):,} 人的中国同量级",
        transform=ax.transAxes, fontsize=8, va="bottom", color="#303e46",
        bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.5))

fig.suptitle("上排：四类常见可视化谬误　　下排：对应修正（同一数据、同一口径）", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, .95))
save(fig, "实验六_任务1_问题图与修正对比.png")

# ============ 6.2 图表选型对比 ============
fig = plt.figure(figsize=(18.5, 5.4))
grid = fig.add_gridspec(1, 5, wspace=.38)

# ① 饼图：角度编码。扇区内/外不再压字，占比统一用图例列出（扇区仅保留角度编码）
ax = fig.add_subplot(grid[0, 0])
ax.pie(area_sum.to_numpy(dtype=float), colors=[COLORS[a] for a in AREA_ORDER],
       startangle=90, counterclock=False,
       wedgeprops=dict(edgecolor="white", linewidth=1))
ax.legend(handles=[Patch(facecolor=COLORS[area], edgecolor="none",
                         label=f"{AREAS[area]} {area_share.loc[area]:.1%}")
                   for area in AREA_ORDER],
          loc="upper center", bbox_to_anchor=(.5, .04), ncol=2, fontsize=7.2,
          frameon=False, handlelength=1.0, handleheight=1.0, handletextpad=.45,
          columnspacing=1.1, labelspacing=.32, borderaxespad=0)
ax.set_title("① 饼图　角度编码\n准确度第 3　观感第 2", fontsize=10)

# ② 水平条形图：公共基线上的位置 / 长度
ax = fig.add_subplot(grid[0, 1])
order = area_sum.sort_values().index
positions = np.arange(len(order))
ax.barh(positions, area_sum.loc[order].to_numpy(dtype=float),
        color=[COLORS[a] for a in order], height=.66)
ax.set_yticks(positions, [AREAS[a] for a in order])
ax.tick_params(axis="y", labelsize=8.5)
for position, area in zip(positions, order):
    ax.text(area_sum.loc[area] + grand * .012, position, f"{area_share.loc[area]:.1%}",
            va="center", fontsize=8)
ax.set_xlim(0, grand * .62)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/10000:.0f}万"))
ax.tick_params(axis="x", labelsize=7.5)
ax.set_xlabel("累计人数", fontsize=8.5)
ax.set_title("② 水平条形图　位置/长度\n准确度第 1　观感第 5", fontsize=10)
ax.grid(axis="x", alpha=.2)

# ③ 堆积百分比条：位置编码，但没有公共基线
ax = fig.add_subplot(grid[0, 2])
left = 0.0
medium = 0   # 6%—15% 的段在水平方向挨得近，标签上下交错，避免压字
for area in AREA_ORDER:
    share = area_share.loc[area] * 100
    ax.barh(0, share, left=left, color=COLORS[area], height=.46,
            edgecolor="white", linewidth=1)
    if share > 15:
        ax.text(left + share / 2, 0, f"{share:.1f}%", ha="center", va="center",
                color="white", fontsize=9, weight="bold")
    elif share > 6:
        ax.text(left + share / 2, .15 if medium % 2 == 0 else -.15,
                f"{share:.1f}%", ha="center", va="center",
                color="white", fontsize=8.5, weight="bold")
        medium += 1
    elif share > 2:
        ax.text(left + share / 2, .40, f"{share:.1f}%", ha="center", va="bottom",
                fontsize=7.5, color="#303e46")
    left += share
ax.annotate("0.9%", xy=(99.55, 0), xytext=(96, -.52), fontsize=7.5, color="#303e46",
            arrowprops=dict(arrowstyle="->", lw=.7, color="#303e46"))
ax.set_ylim(-.75, .75)
ax.set_yticks([])
ax.set_xlim(0, 100)
ax.set_xlabel("占比（%）", fontsize=8.5)
ax.tick_params(axis="x", labelsize=7.5)
ax.set_title("③ 堆积百分比条　位置\n准确度第 2　观感第 4", fontsize=10)

# ④ 矩形树图：面积编码
ax = fig.add_subplot(grid[0, 3])
small = {"Asia": "亚", "Europe": "欧", "Latin America and the Caribbean": "拉",
         "Africa": "非", "Northern America": "北美", "Oceania": "大洋"}
for index, rx, ry, rw, rh in squarify(area_sum.to_numpy(dtype=float), 0, 0, 100, 78):
    area = AREA_ORDER[index]
    ax.add_patch(Rectangle((rx, ry), rw, rh, facecolor=COLORS[area],
                           edgecolor="white", linewidth=2))
    size = 9 if rw > 22 and rh > 22 else 7.5
    ax.text(rx + rw / 2, ry + rh / 2,
            f"{small[area]}\n{area_share.loc[area]:.1%}", ha="center", va="center",
            color="white", fontsize=size, weight="bold")
ax.set(xlim=(0, 100), ylim=(0, 78), aspect="equal")
ax.axis("off")
ax.set_title("④ 矩形树图　面积\n准确度第 4　观感第 3", fontsize=10)

# ⑤ 南丁格尔玫瑰图：半径（按面积正确映射 r ∝ √value）
ax = fig.add_subplot(grid[0, 4], polar=True)
angles = np.linspace(0, 2 * np.pi, len(AREA_ORDER), endpoint=False)
radius = np.sqrt(area_share.to_numpy(dtype=float))
ax.bar(angles, radius, width=2 * np.pi / len(AREA_ORDER) * .92,
       color=[COLORS[a] for a in AREA_ORDER], edgecolor="white", linewidth=1.2,
       bottom=0.0)
ax.set_xticks(angles)
ax.set_xticklabels([AREAS[a] for a in AREA_ORDER], fontsize=7.5)
ax.set_yticks([])
for angle, area in zip(angles, AREA_ORDER):
    ax.text(angle, np.sqrt(area_share.loc[area]) - .06,
            f"{area_share.loc[area]:.1%}", ha="center", va="center",
            fontsize=7.5, color="white", weight="bold")
ax.set_title("⑤ 玫瑰图　半径/面积\n准确度第 5　观感第 1", fontsize=11, pad=16)
ax.text(0, -.28, "半径按 √占比 映射（面积才成比例）", ha="center", transform=ax.transAxes,
        fontsize=7.5, color="#596a70")

fig.suptitle("同一份“六大洲累计占比”数据的五种图表选型：视觉通道越接近“公共基线上的位置”，读数越准确",
             fontsize=12.5)
fig.subplots_adjust(left=.035, right=.975, top=.78, bottom=.13, wspace=.40)
save(fig, "实验六_任务2_图表选型对比.png")

# ============ 6.3 色盲友好性检验 ============
fig, axes = plt.subplots(1, 3, figsize=(17, 5.9))
original = [COLORS[area] for area in AREA_ORDER]
simulated = [mcolors.to_hex(sim(color)) for color in original]
okabe = dict(zip(AREA_ORDER, OKABE))
# 绘图顺序：把两个小扇区（大洋洲 0.86%、北美洲 3.76%）拆开，各自挨着一个大扇区，
# 长标签才不会挤在同一个角度上；数值与配色仍按大洲一一对应，不改变任何数字。
PIE_ORDER = ["Asia", "Oceania", "Europe", "Latin America and the Caribbean",
             "Africa", "Northern America"]

for ax, palette, title, note in [
    (axes[0], dict(zip(AREA_ORDER, original)), "① 原配色（实验四在用）", "实验四的大洲配色"),
    (axes[1], dict(zip(AREA_ORDER, simulated)), "② 红绿色盲（deuteranopia）所见", "Viénot 1999 近似矩阵模拟"),
    (axes[2], okabe, "③ Okabe-Ito 色盲友好方案", "靠明度差，而非红绿差"),
]:
    pie_colors = [palette[area] for area in PIE_ORDER]
    ax.pie(area_sum.reindex(PIE_ORDER).to_numpy(dtype=float), colors=pie_colors,
           labels=[f"{AREAS[area]}\n{color}" for area, color in zip(PIE_ORDER, pie_colors)],
           startangle=90, counterclock=False, labeldistance=1.14,
           textprops=dict(fontsize=7.8, linespacing=1.2),
           wedgeprops=dict(edgecolor="white", linewidth=1.4))
    ax.set_title(title, fontsize=11.5)
    ax.text(0, -.08, note, ha="center", transform=ax.transAxes, fontsize=8.5, color="#596a70")

fig.suptitle("色盲友好性检验：原配色 6 色中有 5 色在模拟后塌缩到同一暖棕/土黄色族，Okabe-Ito 靠明度差拉开距离",
             fontsize=12.5)
fig.subplots_adjust(left=.03, right=.97, top=.80, bottom=.12, wspace=.52)
save(fig, "实验六_任务3_色盲友好性检验.png")

print("=== 6.3 颜色核对 ===")
for area, color in zip(AREA_ORDER, original):
    rgb = np.asarray(mcolors.to_rgb(color))
    gray = sim(color)
    print(f"{AREAS[area]:<6} 原 {color} L={luminance(rgb):.3f}  "
          f"模拟 {mcolors.to_hex(gray)} L={luminance(gray):.3f}")
print("原配色 L 范围", f"{min(luminance(np.asarray(mcolors.to_rgb(c))) for c in original):.3f}",
      f"{max(luminance(np.asarray(mcolors.to_rgb(c))) for c in original):.3f}")
print("Okabe L 范围", f"{min(luminance(np.asarray(mcolors.to_rgb(c))) for c in OKABE):.3f}",
      f"{max(luminance(np.asarray(mcolors.to_rgb(c))) for c in OKABE):.3f}")
for color in OKABE:
    print("Okabe", color, "模拟", mcolors.to_hex(sim(color)),
          f"L={luminance(sim(color)):.3f}")


def closest_pair(colors):
    """两两之间 RGB 欧氏距离最小的一对（越小越容易混淆）。"""
    rgbs = [np.asarray(mcolors.to_rgb(color)) for color in colors]
    best = (9.0, None)
    for i in range(len(rgbs)):
        for j in range(i + 1, len(rgbs)):
            distance = float(np.linalg.norm(rgbs[i] - rgbs[j]))
            if distance < best[0]:
                best = (distance, (AREAS[AREA_ORDER[i]], AREAS[AREA_ORDER[j]]))
    return best


distance_original, pair_original = closest_pair([mcolors.to_hex(sim(c)) for c in original])
distance_okabe, pair_okabe = closest_pair([mcolors.to_hex(sim(c)) for c in OKABE])
print("模拟后最接近的一对（原配色）", pair_original, f"距离 {distance_original:.3f}")
print("模拟后最接近的一对（Okabe）", pair_okabe, f"距离 {distance_okabe:.3f}")
print("可分性提升", f"{distance_okabe / distance_original:.2f} 倍")
print("原配色模拟后 L 跨度", f"{max(luminance(sim(c)) for c in original) - min(luminance(sim(c)) for c in original):.3f}",
      "Okabe", f"{max(luminance(sim(c)) for c in OKABE) - min(luminance(sim(c)) for c in OKABE):.3f}")

# ============ 6.4 旧图复查与重绘 ============
fig, axes = plt.subplots(3, 2, figsize=(16.5, 13.5),
                         gridspec_kw={"width_ratios": [1.0, 1.05]})

# 第一行：实验一大洲饼图（角度编码 + 微小扇区）
original_pie = plt.imread(BASE / "实验一" / "图" / "实验一_任务3_大洲饼图.png")
axes[0, 0].imshow(original_pie)
axes[0, 0].axis("off")
axes[0, 0].set_title("原图：实验一 任务3 大洲饼图\n问题① 角度编码，大洋洲 0.86% 的扇区肉眼不可见", fontsize=10)
mark(axes[0, 0], "问题 ① ② ③", x=.02, y=.93, size=9)

ax = axes[0, 1]
order = area_sum.sort_values(ascending=False).index
positions = np.arange(len(order))
ax.barh(positions, area_sum.loc[order].to_numpy(dtype=float),
        color=[COLORS[area] for area in order], height=.62)
for position, area in zip(positions, order):
    ax.text(area_sum.loc[area] + grand * .01, position,
            f"{area_sum.loc[area]:,}　{area_share.loc[area]:.2%}",
            va="center", fontsize=9)
ax.set_yticks(positions, [AREAS[area] for area in order])
ax.invert_yaxis()
ax.set_xlim(0, grand * .78)
ax.xaxis.set_major_formatter(formatter)
ax.set_xlabel("1980—2013 累计移民人数（人）")
ax.set_title("重绘：排序 + 标绝对值的水平条形图\n（大洋洲 0.86% 的 55,174 人仍足码可见）", fontsize=10.5)
ax.grid(axis="x", alpha=.2)

# 第二行：实验三年度日历热图（单一色标 + 5 行共享色阶）
original_heat = plt.imread(BASE / "实验三" / "图" / "实验三_任务3_年度日历图.png")
axes[1, 0].imshow(original_heat)
axes[1, 0].axis("off")
axes[1, 0].set_title("原图：实验三 任务3 年度日历图\n问题④⑤ 5 行共用 0—42,584 的单一色阶", fontsize=10)
mark(axes[1, 0], "问题 ④ ⑤", x=.02, y=.93, size=9)

ax = axes[1, 1]
top5 = data.nlargest(5, "total")
series_colors = ["#247ba0", "#c95858", "#d17a46", "#618b4a", "#9e6a9e"]
for (_, row), color in zip(top5.iterrows(), series_colors):
    values = row[years].to_numpy(dtype=float)
    ax.plot(years, np.where(values > 0, values, np.nan), color=color, lw=1.8,
            marker="o", ms=2.6, label=f"{name(row['OdName'])}（累计 {int(row['total']):,}）")
ax.set_yscale("log")
ax.yaxis.set_major_formatter(formatter)
ax.set(xlabel="年份", ylabel="年度移民人数（人，对数轴）",
       title="重绘：小倍数折线 + 对数轴（位置编码替代色阶）")
ax.tick_params(axis="x", labelsize=8.5)
ax.legend(fontsize=8.5, loc="upper left", ncol=2, frameon=False)
ax.grid(alpha=.2)
# 峰值标注放到图例右下方、中英两条曲线之间的空白带（对数轴约 1.8 万处），
# 引线只向上指向 2005 年峰值，不再压住图例文字
ax.annotate("中国峰值 42,584（2005）", xy=(2005, 42584), xytext=(2007.0, 18000),
            fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=.8, color="#303e46"))
ax.annotate("英国 1980 年 22,045，2013 年 5,827", xy=(2013, 5827),
            xytext=(1993, 3200), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", lw=.8, color="#303e46"))

# 第三行：实验四桑基图（流量宽度无刻度、小流量不可见）
original_sankey = plt.imread(BASE / "实验四" / "图" / "实验四_任务1_桑基图.png")
axes[2, 0].imshow(original_sankey)
axes[2, 0].axis("off")
axes[2, 0].set_title("原图：实验四 任务1 桑基图\n问题⑥⑦ 12 条流无刻度，细流不可见", fontsize=10)
mark(axes[2, 0], "问题 ⑥ ⑦", x=.02, y=.93, size=9)

ax = axes[2, 1]
pivot = data.pivot_table(index="AreaName", columns="DevName", values="total",
                         aggfunc="sum", fill_value=0).reindex(AREA_ORDER)
pivot = pivot[["Developing regions", "Developed regions"]]
share = pivot.div(pivot.sum(axis=1), axis=0) * 100
dev_colors = {"Developing regions": "#247ba0", "Developed regions": "#d17a46"}
dev_labels = {"Developing regions": "发展中地区", "Developed regions": "发达地区"}
positions = np.arange(len(AREA_ORDER))
left = np.zeros(len(AREA_ORDER))
for column in pivot.columns:
    values = share[column].to_numpy(dtype=float)
    ax.barh(positions, values, left=left, height=.62, color=dev_colors[column],
            label=dev_labels[column], edgecolor="white", linewidth=1)
    for position, (value, offset) in enumerate(zip(values, left)):
        if value > 8:
            ax.text(offset + value / 2, position, f"{value:.1f}%", ha="center",
                    va="center", color="white", fontsize=9, weight="bold")
    left += values
ax.set_yticks(positions, [AREAS[area] for area in AREA_ORDER])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("占该大洲移民的份额（%，每行合计 100%）")
ax.set_title("重绘：按大洲的 100% 堆积条 + 行总量标注", fontsize=10.5)
for position, area in enumerate(AREA_ORDER):
    ax.text(100.9, position, f"{int(pivot.loc[area].sum()):,}", va="center", fontsize=8.5)
ax.legend(fontsize=8.5, loc="lower center", bbox_to_anchor=(.5, -.30), ncol=2, frameon=False)
ax.grid(axis="x", alpha=.2)

fig.suptitle("三张前序实验图的复查与重绘：左边是原图（只读引用），右边是改掉编码缺陷后的版本",
             fontsize=13)
fig.tight_layout(rect=(0, 0, 1, .955), h_pad=2.2)
save(fig, "实验六_任务4_旧图复查与重绘.png")

print("=== 6.4 桑基复查数据 ===")
print(pivot.to_string())
print((share.round(1)).to_string())

# ============ 6.5 坐标设定与叙事偏差 ============
fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.2), sharex=True)
settings = [
    ("① 线性 y 轴，从 0 起（真实）", lambda ax: ax.set_ylim(0, 46000),
     "故事：34 年从 5,123 人涨到 34,129 人，\n2005 年见顶后高位震荡——稳步上涨。"),
    ("② 截断 y 轴（从 20,000 起）", lambda ax: ax.set_ylim(20000, 46000),
     "故事：2005 年前后“爆发式”冲顶又崩落，\n80—90 年代被整段切掉，看不见。"),
    ("③ 对数 y 轴（1,000—60,000）", lambda ax: (ax.set_yscale("log"), ax.set_ylim(1000, 60000)),
     "故事：几乎是一条平坦曲线，\n增长被压缩，“剧烈波动”消失了。"),
]
for ax, (title, setter, story) in zip(axes, settings):
    ax.plot(years, china, color="#c95858", lw=2.2, marker="o", ms=3.2)
    ax.fill_between(years, 1, china, color="#c95858", alpha=.12)
    setter(ax)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("年份")
    ax.set_ylabel("中国年度移民人数（人）")
    ax.yaxis.set_major_formatter(formatter)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(alpha=.2)
    ax.text(.03, .96, story, transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(facecolor="white", edgecolor="#c9cfd2", alpha=.9,
                      boxstyle="round,pad=0.3"))

axes[0].annotate("1980 年 5,123", xy=(1980, 5123), xytext=(1981, 16000), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=.8, color="#303e46"))
axes[0].annotate("2013 年 34,129", xy=(2013, 34129), xytext=(2000, 38000), fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=.8, color="#303e46"))
axes[1].text(.03, .05, f"低于 20,000 的 {int((china < 20000).sum())} 个年份完全消失",
             transform=axes[1].transAxes, fontsize=8.5, color=RED)
axes[2].text(.03, .05, "对数轴用于“跨数量级”比较，\n不适合讲“增长有多快”", transform=axes[2].transAxes,
             fontsize=8.5, color="#596a70")
fig.suptitle("同一列中国数据、三种坐标设定：坐标不是中立的，它替你决定了故事怎么讲", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, .92))
save(fig, "实验六_任务5_坐标设定与叙事偏差.png")

# ============ 报告要引用的关键数字 ============
print("=== 关键统计（供报告核对）===")
print("国家数", len(data), "总量", int(grand))
print("大洲", {AREAS[a]: (int(area_sum[a]), f"{area_share[a]:.2%}") for a in AREA_ORDER})
print("top5 占比", f"{top5['total'].sum() / grand:.2%}", "其他", int(grand - top5["total"].sum()))
print("年度最低", int(annual.idxmin()), int(annual.min()), "最高", int(annual.idxmax()), int(annual.max()))
print("首个 >=25 万", [int(y) for y in years if annual[y] >= 250000])
print("1993", int(annual[1993]))
print("中国 1980/2013", int(china[0]), int(china[-1]), "峰值", int(china.max()),
      int(years[int(china.argmax())]))
print("中国 2004/2005", int(china[24]), int(china[25]))
print("日本累计", 27707, "中国累计", 659962, "比值", f"{27707/659962:.3f}",
      f"即约 1/{659962/27707:.1f}")
print("年度 2005", int(annual[2005]), "2013", int(annual[2013]), "2001", int(annual[2001]))

# 6.4 原图存在性自检
for path in ["实验一/图/实验一_任务3_大洲饼图.png",
             "实验三/图/实验三_任务3_年度日历图.png",
             "实验四/图/实验四_任务1_桑基图.png"]:
    assert (BASE / path).exists(), path
print("=== 引用的前序实验原图全部存在 ===")
print("=== done ===")
