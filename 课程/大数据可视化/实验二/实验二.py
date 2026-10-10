# -*- coding: utf-8 -*-
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\omori\Omori-s-Codings\课程\大数据可视化"
sys.path.insert(0, BASE)
from viz_common import BASE, YEARS, load_canada

OUT = os.path.join(BASE, "实验二", "图")

CN = {
    "China": "中国", "Japan": "日本", "India": "印度",
    "Philippines": "菲律宾", "Pakistan": "巴基斯坦",
    "United Kingdom of Great Britain and Northern Ireland": "英国",
    "United States of America": "美国",
    "Iran (Islamic Republic of)": "伊朗",
    "Sri Lanka": "斯里兰卡", "Republic of Korea": "韩国",
    "Poland": "波兰", "Lebanon": "黎巴嫩", "France": "法国",
    "Iraq": "伊拉克", "Palau": "帕劳",
    "Marshall Islands": "马绍尔群岛", "Western Sahara": "西撒哈拉",
}


def cn(name):
    return CN.get(name, name)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def kfmt(x, pos=None):
    return f"{int(x):,}"


def row_vals(df, i):
    return df[years].iloc[i].astype(float).values


ca, years = load_canada()
ca["tot"] = ca[years].sum(axis=1)
top = ca.sort_values("tot", ascending=False)
top3 = top.head(3).reset_index(drop=True)
nz = ca[ca["tot"] > 0].sort_values("tot")
bot3 = nz.head(3).reset_index(drop=True)
COLORS3 = ["#d62728", "#1f77b4", "#2ca02c"]

# ============ 实验二 任务1 折线图 + 面积图 ============
fig, ax = plt.subplots(figsize=(11, 5))
for i in range(len(top3)):
    ax.plot(years, row_vals(top3, i), marker="o", label=cn(top3.iloc[i]["OdName"]), color=COLORS3[i])
ax.set_title("对加拿大移民最多的 3 个来源国：1980-2013 年折线图")
ax.set_xlabel("年份")
ax.set_ylabel("移民人数（人）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
save(fig, "实验二_任务1_最多3国折线图.png")

fig, ax = plt.subplots(figsize=(11, 5))
for i in range(len(bot3)):
    ax.plot(years, row_vals(bot3, i), marker="o", label=cn(bot3.iloc[i]["OdName"]), color=COLORS3[i])
ax.set_title("对加拿大移民最少的 3 个来源国：1980-2013 年折线图")
ax.set_xlabel("年份")
ax.set_ylabel("移民人数（人）")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
save(fig, "实验二_任务1_最少3国折线图.png")

fig, ax = plt.subplots(figsize=(11, 5))
for i in range(len(top3)):
    v = row_vals(top3, i)
    ax.fill_between(years, v, alpha=0.4, label=cn(top3.iloc[i]["OdName"]), color=COLORS3[i])
    ax.plot(years, v, color=COLORS3[i], linewidth=1.2)
ax.set_title("对加拿大移民最多的 3 个来源国：1980-2013 年面积图")
ax.set_xlabel("年份")
ax.set_ylabel("移民人数（人）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
save(fig, "实验二_任务1_最多3国面积图.png")

# ============ 实验二 任务2 中国 vs 日本 ============
china_df = ca[ca["OdName"] == "China"].reset_index(drop=True)
japan_df = ca[ca["OdName"] == "Japan"].reset_index(drop=True)
cvals = row_vals(china_df, 0)
jvals = row_vals(japan_df, 0)
fig, ax1 = plt.subplots(figsize=(11, 5.5))
ax1.plot(years, cvals, marker="o", color="#d62728", label="中国（左轴）")
ax1.set_xlabel("年份")
ax1.set_ylabel("中国移民人数（人）", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#d62728")
ax1.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax2 = ax1.twinx()
ax2.plot(years, jvals, marker="s", color="#1f77b4", label="日本（右轴）")
ax2.set_ylabel("日本移民人数（人）", color="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#1f77b4")
ax2.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax1.set_title("中国 vs 日本 移民加拿大人口分布（1980-2013）")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left")
ax1.grid(alpha=0.3)
fig.tight_layout()
save(fig, "实验二_任务2_中日分布对比.png")

# ============ 实验二 任务3 中国柱状图 + 标记 ============
colors = ["#f39c12" if 1993 <= y <= 2003 else "#3b7dd8" for y in years]
fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar([str(y) for y in years], cvals, color=colors)
ax.set_title("中国 1980-2013 年移民加拿大人数（1993-2003 已标记）")
ax.set_xlabel("年份")
ax.set_ylabel("移民人数（人）")
ax.tick_params(axis="x", rotation=90, labelsize=7)
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
import matplotlib.patches as mpatches
ax.legend(handles=[mpatches.Patch(color="#f39c12", label="1993-2003"),
                   mpatches.Patch(color="#3b7dd8", label="其余年份")])
for y0 in [1993, 2003]:
    i = years.index(y0)
    ax.axvline(i, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
fig.tight_layout()
save(fig, "实验二_任务3_中国柱状图标记.png")

# ============ 实验二 任务4 水平条形图 ============
t10 = ca.sort_values(2013, ascending=False).head(10)
labels = [cn(n) for n in t10["OdName"]][::-1]
vals = t10[2013].astype(float).values[::-1]
fig, ax = plt.subplots(figsize=(9.5, 6))
bars = ax.barh(labels, vals, color="#3b7dd8")
ax.set_title("2013 年移民加拿大人数最多的 10 个来源国")
ax.set_xlabel("移民人数（人）")
ax.xaxis.set_major_formatter(plt.FuncFormatter(kfmt))
for b, v in zip(bars, vals):
    ax.text(v, b.get_y() + b.get_height() / 2, f" {int(v):,}", va="center", ha="left", fontsize=9)
fig.tight_layout()
save(fig, "实验二_任务4_2013前10水平条形图.png")

# 打印关键数字
print("=== 任务1 最多3国 ===")
for i in range(len(top3)):
    print(cn(top3.iloc[i]["OdName"]), "tot", int(top3.iloc[i]["tot"]), "1980", int(row_vals(top3, i)[0]), "2013", int(row_vals(top3, i)[-1]))
print("=== 任务1 最少3国 ===")
for i in range(len(bot3)):
    print(cn(bot3.iloc[i]["OdName"]), "tot", int(bot3.iloc[i]["tot"]))
print("=== 任务2 中日 ===")
print("中国 tot", int(china_df.iloc[0]["tot"]), "1980", int(cvals[0]), "1993", int(cvals[years.index(1993)]), "2003", int(cvals[years.index(2003)]), "2013", int(cvals[-1]))
print("日本 tot", int(japan_df.iloc[0]["tot"]), "1980", int(jvals[0]), "2013", int(jvals[-1]))
print("=== 任务4 2013前10 ===")
for i in range(len(t10)):
    print(cn(t10.iloc[i]["OdName"]), int(t10.iloc[i][2013]))
print("=== done ===")