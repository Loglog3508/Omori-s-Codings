# -*- coding: utf-8 -*-
"""实验五：把前四个实验的分析成果整理为可交付的可视化输出。

实验一至四解决的是“用什么图、怎么画”，本实验解决“画完怎么交付”：
分辨率与格式、配色主题、版式组织、注释完整性、中文字体可用性五个约束。
数据口径延续实验一：加拿大外来移民（Type=Immigrants & Coverage=Foreigners），1980—2013。
"""

from pathlib import Path
import os
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import font_manager as fm
from matplotlib.gridspec import GridSpec
import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from viz_common import load_canada, YEARS

OUT = Path(__file__).resolve().parent / "图"
EXPORT = OUT / "导出"
for _d in (OUT, EXPORT):
    _d.mkdir(parents=True, exist_ok=True)

# 中英文名称对照（与实验一至四保持一致）
NAMES = {
    "India": "印度", "China": "中国",
    "United Kingdom of Great Britain and Northern Ireland": "英国",
    "Philippines": "菲律宾", "Pakistan": "巴基斯坦",
    "United States of America": "美国", "France": "法国", "Iraq": "伊拉克",
    "Republic of Korea": "韩国", "Iran (Islamic Republic of)": "伊朗",
}
AREA_ORDER = ["Asia", "Europe", "Latin America and the Caribbean",
              "Africa", "Northern America", "Oceania"]
AREAS = {
    "Asia": "亚洲", "Europe": "欧洲",
    "Latin America and the Caribbean": "拉美和加勒比",
    "Africa": "非洲", "Northern America": "北美洲", "Oceania": "大洋洲",
}
# 课程主题配色：六大洲语义色 + 中性底色，跨图复用
COLORS = {
    "Asia": "#247ba0", "Europe": "#d17a46", "Northern America": "#618b4a",
    "Africa": "#9e6a9e", "Latin America and the Caribbean": "#c95858",
    "Oceania": "#8a9283",
}
THEME = {"bg": "#fbfbfb", "grid": "#e6e6e6", "text": "#333333", "note": "#777777"}
SOURCE = ("数据来源：UN MigFlow 2015 修订版；口径 Type=Immigrants & Coverage=Foreigners；"
          "1980—2013 共 34 年")


def name(value):
    return NAMES.get(value, value)


def kb(path):
    return os.path.getsize(path) / 1024


def save(fig, filename, dpi=150):
    fig.savefig(OUT / filename, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {filename}")


def prepare():
    data, years = load_canada()
    data["total"] = data[YEARS].sum(axis=1)
    annual = data[YEARS].sum(axis=0)
    area_tot = data.groupby("AreaName")["total"].sum().reindex(AREA_ORDER)
    dev_tot = data.groupby("DevName")["total"].sum()
    return data, years, annual, area_tot, dev_tot


# ---------------------------------------------------------------- 5.1
def task1_formats(data):
    """同一张图导出为不同分辨率与不同格式，比较像素、体积与观感。"""
    top = data.nlargest(10, 2013).sort_values(2013)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.barh([name(v) for v in top["OdName"]], top[2013].values,
            color=COLORS["Asia"], height=.68)
    for y, v in enumerate(top[2013].values):
        ax.text(v, y, f" {v:,}", va="center", fontsize=9)
    ax.set(title="2013 年加拿大外来移民前 10 来源国", xlabel="移民人数（人）")
    ax.set_xlim(0, top[2013].max() * 1.16)
    ax.grid(axis="x", color=THEME["grid"])
    ax.set_axisbelow(True)
    fig.tight_layout()

    pngs = []
    for dpi in (72, 150, 300):
        p = EXPORT / f"task1_{dpi}dpi.png"
        fig.savefig(p, dpi=dpi)
        pngs.append(p)
    vectors = []
    for ext in ("pdf", "svg"):
        p = EXPORT / f"task1.{ext}"
        fig.savefig(p)
        vectors.append(p)
    plt.close(fig)

    # 导出清单
    lines = ["实验五 任务1 基准图导出清单", "=" * 46]
    for p in pngs:
        h, w = mpimg.imread(p).shape[:2]
        lines.append(f"{p.name:<18} 位图 PNG   {w}×{h} px  {kb(p):6.1f} KB")
    for p in vectors:
        lines.append(f"{p.name:<18} 矢量 {p.suffix[1:].upper():<5} {kb(p):6.1f} KB（可无损缩放）")
    lines.append("")
    lines.append("结论：屏幕浏览取 150 dpi；报告/打印插图取 300 dpi；")
    lines.append("需要任意放大或二次排版时优先交付 PDF/SVG 矢量格式。")
    (EXPORT / "导出清单.txt").write_text("\n".join(lines), encoding="utf-8")
    print("  saved 导出/task1_*.png|pdf|svg + 导出清单.txt")

    # 对比图：左边体积与像素，右边同区域裁剪放大
    files = pngs + vectors
    labels, pixels = [], []
    for p in files:
        if p.suffix == ".png":
            h, w = mpimg.imread(p).shape[:2]
            # 刻度标签只留导出规格，像素尺寸改到柱顶，避免相邻标签横向相压
            labels.append(f"PNG\n{p.stem.split('_')[-1]}")
            pixels.append(f"\n{w}×{h} px")
        else:
            labels.append(f"{p.suffix[1:].upper()}\n矢量")
            pixels.append("")
    sizes = [kb(p) for p in files]

    fig = plt.figure(figsize=(14, 5.2))
    gs = GridSpec(1, 3, fig, width_ratios=[1.3, 1, 1], wspace=.28)
    ax0 = fig.add_subplot(gs[0, 0])
    bar_colors = ["#a8c6d8", "#5b93b5", "#247ba0", "#d17a46", "#9e6a9e"]
    ax0.bar(range(len(files)), sizes, color=bar_colors, width=.6)
    for i, s in enumerate(sizes):
        ax0.text(i, s, f"{s:.0f} KB{pixels[i]}", ha="center", va="bottom", fontsize=8.5)
    ax0.set_xticks(range(len(files)))
    ax0.set_xticklabels(labels, fontsize=8.5)
    ax0.set_ylim(0, max(sizes) * 1.26)
    ax0.set(ylabel="文件体积（KB）", title="（a）同一张图五种输出的体积与像素尺寸")
    ax0.grid(axis="y", color=THEME["grid"])
    ax0.set_axisbelow(True)

    def crop(img):
        h, w = img.shape[:2]
        return img[0:int(h * .26), 0:int(w * .58)]

    for idx, (p, tag) in enumerate(((pngs[0], "72 dpi"), (pngs[2], "300 dpi")), start=1):
        ax = fig.add_subplot(gs[0, idx])
        ax.imshow(crop(mpimg.imread(p)), interpolation="nearest")
        ax.axis("off")
        # 标题折成两行，避免长标题向左压到左侧子图的“0”刻度
        ax.set_title(f"（{'bc'[idx - 1]}）{tag} 同区域放大\n"
                     + ("文字与坐标轴出现明显锯齿" if idx == 1 else "边缘平滑、无锯齿"),
                     fontsize=9)
    fig.suptitle("输出格式与分辨率对比", fontsize=14, fontweight="bold", y=1.0)
    save(fig, "实验五_任务1_输出格式与分辨率对比.png")


# ---------------------------------------------------------------- 5.2
def draw_area_pie(ax, vals, labels, pct, colors, text_color=None):
    """画六大洲占比饼图：<5% 的小切片不挤在圆周上，改用引线引到顶部两侧。

    北美洲 3.8% 与大洋洲 0.9% 相邻且太小，弧上放不下名字+百分比，
    因此把它们合并成“名字 百分比”的标注，左右各一条，其余四片照常标注。
    """
    small = [p < 5 for p in pct]
    textprops = {"color": text_color} if text_color else None
    wedges, _texts, _autotexts = ax.pie(
        vals, labels=["" if s else lab for s, lab in zip(small, labels)],
        autopct=lambda p: f"{p:.1f}%" if p >= 5 else "",
        startangle=90, counterclock=False, colors=colors, textprops=textprops,
        radius=.92)
    # 上方留出一圈空白，两条引线标注才放得下、又不会压到扇区标签
    ax.set_xlim(-1.32, 1.32)
    ax.set_ylim(-1.32, 1.32)
    side = -1
    for w, s, lab, p in zip(wedges, small, labels, pct):
        if not s:
            continue
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        tx, ty = side * .22, 1.15
        ax.text(tx, ty, f"{lab} {p:.1f}%", ha="right" if side < 0 else "left",
                va="center", fontsize=9, color=text_color or THEME["text"])
        # 引线用 Line2D 画：annotate 的箭头会把文字包围盒撑到箭头末端，
        # 反而更容易与邻片标签的包围盒相交
        ax.plot([tx, np.cos(ang) * .93], [ty - .07, np.sin(ang) * .93],
                color=text_color or THEME["text"], lw=.7, clip_on=False, zorder=0)
        side = 1


def task2_theme(area_tot):
    """默认配色与统一主题的对比：同一份数据、两套视觉规则。"""
    vals = area_tot.values
    labels = [AREAS[a] for a in AREA_ORDER]
    pct = vals / vals.sum() * 100
    default_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.4))
    fig.suptitle("统一配色主题前后对比", fontsize=15, fontweight="bold")

    # 上排：matplotlib 默认
    draw_area_pie(axes[0, 0], vals, labels, pct, default_cycle[:6])
    axes[0, 0].set_title("（a）默认配色 · 饼图", fontsize=11)
    axes[0, 1].bar(labels, vals, color=default_cycle[:6])
    axes[0, 1].set_title("（b）默认配色 · 柱状图（每类颜色随出现顺序变化）", fontsize=11)
    axes[0, 1].tick_params(axis="x", rotation=20)
    axes[0, 1].grid(axis="y", color=THEME["grid"])
    axes[0, 1].set_axisbelow(True)

    # 下排：课程主题（语义色 + 浅底 + 去边框 + 统一字色）
    theme_colors = [COLORS[a] for a in AREA_ORDER]
    for ax in axes[1]:
        ax.set_facecolor(THEME["bg"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(THEME["grid"])
        ax.tick_params(colors=THEME["text"])
    draw_area_pie(axes[1, 0], vals, labels, pct, theme_colors, text_color=THEME["text"])
    axes[1, 0].set_title("（c）课程主题配色 · 饼图（大洲语义色固定）", fontsize=11,
                         color=THEME["text"])
    axes[1, 0].legend([f"{AREAS[a]} {COLORS[a]}" for a in AREA_ORDER],
                      loc="center left", bbox_to_anchor=(1.0, .5), frameon=False, fontsize=8)
    axes[1, 1].bar(labels, vals, color=theme_colors)
    axes[1, 1].set_title("（d）课程主题配色 · 柱状图（同色系跨图一致）", fontsize=11,
                         color=THEME["text"])
    axes[1, 1].tick_params(axis="x", rotation=20)
    axes[1, 1].grid(axis="y", color=THEME["grid"])
    axes[1, 1].set_axisbelow(True)
    for i, v in enumerate(vals):
        axes[1, 1].text(i, v, f"{pct[i]:.1f}%", ha="center", va="bottom", fontsize=9,
                        color=THEME["text"])

    fig.text(.5, .012, "六类大洲在四张图中使用同一组色值，读者才能把颜色当作索引而"
                       "不是装饰——这就是“主题”的价值。",
             ha="center", fontsize=9.5, color=THEME["note"])
    fig.tight_layout(rect=(0, .03, 1, .95))
    save(fig, "实验五_任务2_统一配色主题对比.png")


# ---------------------------------------------------------------- 5.3
def task3_dashboard(data, years, annual, area_tot, dev_tot):
    """用 GridSpec 把四个关键面板拼成一页式仪表板，统一标题层级与边距。"""
    fig = plt.figure(figsize=(15, 9.6))
    gs = GridSpec(2, 2, fig, hspace=.34, wspace=.24,
                  left=.075, right=.965, top=.845, bottom=.10)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_facecolor(THEME["bg"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.grid(color=THEME["grid"])
        ax.set_axisbelow(True)

    # 面板 1：年度总量
    ax1.fill_between(years, annual.values, color=COLORS["Asia"], alpha=.20)
    ax1.plot(years, annual.values, color=COLORS["Asia"], lw=2)
    imax, imin = int(np.argmax(annual.values)), int(np.argmin(annual.values))
    ax1.scatter([years[imax]], [annual.values[imax]], color="#c95858", zorder=5)
    ax1.annotate(f"峰值 {annual.values[imax]:,.0f}\n（{years[imax]}）",
                 (years[imax], annual.values[imax]), textcoords="offset points",
                 xytext=(-58, 6), fontsize=9, color="#c95858")
    ax1.annotate(f"谷值 {annual.values[imin]:,.0f}\n（{years[imin]}）",
                 (years[imin], annual.values[imin]), textcoords="offset points",
                 xytext=(8, 22), fontsize=9, color=THEME["note"])
    ax1.set(title="① 年度流入总量", ylabel="移民人数（人）", xlabel="年份")
    ax1.set_ylim(0, annual.max() * 1.28)

    # 面板 2：大洲累计占比
    order = area_tot.sort_values()
    ax2.barh([AREAS[a] for a in order.index], order.values,
             color=[COLORS[a] for a in order.index], height=.62)
    for y, (a, v) in enumerate(order.items()):
        ax2.text(v, y, f" {v:,.0f}（{v / area_tot.sum() * 100:.1f}%）",
                 va="center", fontsize=9)
    ax2.set(title="② 六大洲累计来源占比", xlabel="累计移民人数（人）")
    ax2.set_xlim(0, area_tot.max() * 1.42)

    # 面板 3：2013 年前 8
    top8 = data.nlargest(8, 2013).sort_values(2013)
    ax3.barh([name(v) for v in top8["OdName"]], top8[2013].values,
             color=[COLORS["Asia"] if a == "Asia" else "#8ba7bb"
                    for a in top8["AreaName"]], height=.62)
    for y, v in enumerate(top8[2013].values):
        ax3.text(v, y, f" {v:,}", va="center", fontsize=9)
    ax3.set(title="③ 2013 年来源国前 8（深色为亚洲）", xlabel="当年移民人数（人）")
    ax3.set_xlim(0, top8[2013].max() * 1.2)

    # 面板 4：发展中 / 发达地区
    left = 0.0
    for dev, color, label in (("Developing regions", "#c95858", "发展中地区"),
                              ("Developed regions", COLORS["Asia"], "发达地区")):
        v = float(dev_tot[dev])
        ax4.barh([""], [v], left=left, color=color, height=.5)
        ax4.text(left + v / 2, 0, f"{label}\n{v:,.0f} 人\n{v / dev_tot.sum() * 100:.1f}%",
                 ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        left += v
    ax4.set_xlim(0, dev_tot.sum())
    ax4.set_yticks([])
    ax4.grid(False)
    ax4.set(title="④ 按发展程度划分的累计占比", xlabel="累计移民人数（人）")

    fig.suptitle("加拿大外来移民概览（1980—2013）", fontsize=21, fontweight="bold")
    fig.text(.5, .912, SOURCE, ha="center", fontsize=9.5, color=THEME["note"])
    fig.text(.965, .028, "图 5-3  一页式仪表板：四个面板共用同一套配色、字号与留白规则",
             ha="right", fontsize=8.5, color=THEME["note"])
    save(fig, "实验五_任务3_一页式仪表板.png", dpi=300)


# ---------------------------------------------------------------- 5.4
def task4_annotation(data):
    """同一张图的裸版与规范版：注释不是装饰，是让图能独立被读懂。"""
    china = data[data["OdName"] == "China"][YEARS].values[0]
    mean = china.mean()
    peak_year = YEARS[int(np.argmax(china))]
    peak_val = china.max()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    # （a）裸图
    axes[0].bar(YEARS, china, color="#b9b9b9")
    # 自动定位会生成 1975 / 2020 这类落在数据范围外的刻度，标签悬在轴外互相贴住，
    # 因此仍用默认外观，但把刻度显式限定在数据范围内
    axes[0].set_xticks(range(1980, 2014, 8))
    axes[0].text(.5, -.19, "（a）裸图：没有标题、单位、来源与关键标注",
                 transform=axes[0].transAxes, ha="center", fontsize=9.5, color="#8a8a8a")

    # （b）规范版
    ax = axes[1]
    ax.set_facecolor(THEME["bg"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color=THEME["grid"])
    ax.set_axisbelow(True)
    ax.bar(YEARS, china, color=COLORS["Asia"], width=.72)
    ax.axhline(mean, color="#c95858", ls="--", lw=1.2)
    ax.text(1980.4, mean * 1.06, f"34 年均值 {mean:,.0f} 人", fontsize=9, color="#c95858")
    ax.annotate(f"峰值 {peak_val:,} 人（{peak_year}）",
                xy=(peak_year, peak_val), xytext=(peak_year - 12, peak_val * .92),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1),
                fontsize=10, color="#333333")
    ax.set(title="中国来源移民人数（1980—2013）", ylabel="移民人数（人）", xlabel="年份")
    ax.set_ylim(0, peak_val * 1.18)
    ax.set_xticks(range(1980, 2014, 4))
    ax.text(.5, -.19, "（b）规范版：标题+单位+均值参考线+峰值标注+来源脚注",
            transform=ax.transAxes, ha="center", fontsize=9.5, color=THEME["note"])

    fig.suptitle("注释规范对比", fontsize=15, fontweight="bold", y=.99)
    fig.text(.985, -.02, SOURCE + "；图 5-4  注释规范示意", ha="right",
             fontsize=8.5, color=THEME["note"])
    fig.tight_layout(rect=(0, .04, 1, .95))
    save(fig, "实验五_任务4_注释规范对比.png")


# ---------------------------------------------------------------- 5.5
def task5_fonts(years, annual):
    """中文字体缺失、负号显示两类典型“输出事故”的对照复现。

    三个面板先按各自 rcParams 渲染成独立 PNG，再拼合——因为字体是在
    savefig 绘制阶段解析的，用 rc_context 包住绘图语句并不能真正改变输出。
    """
    available = {f.name for f in fm.fontManager.ttflist}
    has_simhei = "SimHei" in available
    has_yahei = "Microsoft YaHei" in available

    configs = [
        (["DejaVu Sans"], True,
         "① font.sans-serif=['DejaVu Sans']\n中文全部渲染为方块（缺字形）"),
        (["SimHei", "DejaVu Sans"], True,
         "② font.sans-serif=['SimHei']\n中文正常，但 unicode_minus=True 时负号为短横"
         if has_simhei else
         "② 本机未安装 SimHei，回退 Microsoft YaHei"),
        (["Microsoft YaHei", "SimHei", "DejaVu Sans"], False,
         "③ 微软雅黑 + axes.unicode_minus=False\n中文与负号（−20,000）均正常"),
    ]
    if not has_yahei:
        configs[2] = (["SimHei", "DejaVu Sans"], False,
                      "③ 本机未安装微软雅黑，回退 SimHei；负号已修正")

    shots = []
    for i, (fonts, minus, _note) in enumerate(configs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with plt.rc_context({"font.sans-serif": fonts,
                                 "axes.unicode_minus": minus}):
                f2, a2 = plt.subplots(figsize=(6.2, 4.0))
                a2.fill_between(years, annual.values, color=COLORS["Asia"], alpha=.18)
                a2.plot(years, annual.values, color=COLORS["Asia"], lw=2)
                a2.set(title="中文字体渲染测试", ylabel="移民人数（人）", xlabel="年份")
                # 显式给定刻度，避免自动定位把 1975 / 2015 / -50000 这类
                # 越界刻度也画出来，在左下角与相邻刻度标签相压
                a2.set_ylim(-30000, 300000)
                a2.set_yticks([-20000, 0, 50000, 100000, 150000, 200000, 250000, 300000])
                a2.set_xticks(range(1980, 2014, 5))
                a2.grid(color=THEME["grid"])
                a2.set_axisbelow(True)
                p = EXPORT / f"task5_font_{i + 1}.png"
                f2.savefig(p, dpi=110, bbox_inches="tight")
                plt.close(f2)
        shots.append(p)

    fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.0))
    for ax, p, (_f, _m, note) in zip(axes, shots, configs):
        ax.imshow(mpimg.imread(p), interpolation="lanczos")
        ax.axis("off")
        ax.set_title(note.split("\n")[0], fontsize=10.5)
        ax.text(.5, -.06, note.split("\n")[1], transform=ax.transAxes,
                ha="center", va="top", fontsize=9.5, color=THEME["note"])
    fig.suptitle("中文字体与负号显示对比", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, .04, 1, .95))
    save(fig, "实验五_任务5_中文字体显示对比.png")


def main():
    data, years, annual, area_tot, dev_tot = prepare()
    print(f"数据：{len(data)} 个来源国，{years[0]}—{years[-1]}，"
          f"累计 {int(data['total'].sum()):,} 人")
    print("5.1 输出格式与分辨率 ...")
    task1_formats(data)
    print("5.2 统一配色主题 ...")
    task2_theme(area_tot)
    print("5.3 一页式仪表板 ...")
    task3_dashboard(data, years, annual, area_tot, dev_tot)
    print("5.4 注释规范对比 ...")
    task4_annotation(data)
    print("5.5 中文字体显示 ...")
    task5_fonts(years, annual)
    print("完成：5 张图 + 导出文件已写入", OUT)


if __name__ == "__main__":
    main()
