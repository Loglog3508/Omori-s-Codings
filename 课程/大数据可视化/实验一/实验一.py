# -*- coding: utf-8 -*-
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\omori\Omori-s-Codings\课程\大数据可视化"
sys.path.insert(0, BASE)
from viz_common import BASE, YEARS, DECADES, load_canada, load_australia

OUT = os.path.join(BASE, "实验一", "图")

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
AREA_CN = {
    "Asia": "亚洲", "Europe": "欧洲",
    "Latin America and the Caribbean": "拉美和加勒比",
    "Africa": "非洲", "Northern America": "北美洲", "Oceania": "大洋洲",
}
DEV_CN = {"Developed regions": "发达地区", "Developing regions": "发展中地区"}
DEC_CN = ["80年代", "90年代", "00年代", "10-13年"]


def cn(name):
    return CN.get(name, name)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def kfmt(x, pos=None):
    return f"{int(x):,}"


ca, years = load_canada()
ca["tot"] = ca[years].sum(axis=1)
top = ca.sort_values("tot", ascending=False)
top5 = top.head(5).reset_index(drop=True)
area_order = ["Asia", "Europe", "Latin America and the Caribbean", "Africa", "Northern America", "Oceania"]
dev_order = ["Developed regions", "Developing regions"]

# ============ 实验一 任务1 柱状图 ============
t1 = top.head(15)
fig, ax = plt.subplots(figsize=(11, 5.5))
x = [cn(n) for n in t1["OdName"]]
y = t1["tot"].values
bars = ax.bar(x, y, color="#3b7dd8")
ax.set_title("1980-2013 年加拿大移民来源国累计人数（前 15 位）")
ax.set_xlabel("来源国")
ax.set_ylabel("累计移民人数（人）")
ax.tick_params(axis="x", rotation=45)
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
for b, v in zip(bars, y):
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
fig.tight_layout()
save(fig, "实验一_任务1_来源国柱状图.png")

# ============ 实验一 任务2 分组柱状图 ============
dec_cols = {d[0]: [y for y in years if d[1] <= y <= d[2]] for d in DECADES}
top5_dec = top5.copy()
for i, d in enumerate(DECADES):
    top5_dec[DEC_CN[i]] = top5_dec[dec_cols[d[0]]].sum(axis=1)

width = 0.2
xx = np.arange(len(top5_dec))
fig, ax = plt.subplots(figsize=(11, 5.5))
for i, dcn in enumerate(DEC_CN):
    vals = top5_dec[dcn].values
    ax.bar(xx + (i - 1.5) * width, vals, width, label=dcn)
ax.set_xticks(xx)
ax.set_xticklabels([cn(n) for n in top5_dec["OdName"]])
ax.set_title("加拿大移民来源国前 5 位 × 不同年代分组柱状图")
ax.set_xlabel("来源国")
ax.set_ylabel("移民人数（人）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax.legend(title="年代")
fig.tight_layout()
save(fig, "实验一_任务2_前5来源国分组柱状图.png")

# 第二张：各大洲 × 年代 分组柱状图
fig, ax = plt.subplots(figsize=(11, 5.5))
xx = np.arange(len(area_order))
for i, d in enumerate(DECADES):
    vals = [ca[ca["AreaName"] == a][dec_cols[d[0]]].values.sum() for a in area_order]
    ax.bar(xx + (i - 1.5) * width, vals, width, label=DEC_CN[i])
ax.set_xticks(xx)
ax.set_xticklabels([AREA_CN[a] for a in area_order])
ax.set_title("加拿大移民来源大洲 × 不同年代分组柱状图")
ax.set_xlabel("来源大洲")
ax.set_ylabel("移民人数（人）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax.legend(title="年代")
fig.tight_layout()
save(fig, "实验一_任务2_大洲年代分组柱状图.png")

# ============ 实验一 任务3 饼图 ============
area_sum = ca.groupby("AreaName")["tot"].sum().reindex(area_order)
fig, ax = plt.subplots(figsize=(8, 8))
ax.pie(area_sum.values, labels=[AREA_CN[a] for a in area_order],
       autopct="%.1f%%", startangle=90, counterclock=False,
       pctdistance=0.75, labeldistance=1.08)
ax.set_title("加拿大移民来源国所属大洲（AreaName）构成")
fig.tight_layout()
save(fig, "实验一_任务3_大洲饼图.png")

dev_sum = ca.groupby("DevName")["tot"].sum().reindex(dev_order)
fig, ax = plt.subplots(figsize=(7.5, 7.5))
ax.pie(dev_sum.values, labels=[DEV_CN[d] for d in dev_order],
       autopct="%.1f%%", startangle=90, counterclock=False,
       pctdistance=0.65, labeldistance=1.1)
ax.set_title("加拿大移民来源国所属地区（DevName）构成")
fig.tight_layout()
save(fig, "实验一_任务3_地区饼图.png")

# ============ 实验一 任务4 堆积百分比柱状图 + 旭日图 ============
pivot = ca.pivot_table(index="AreaName", columns="DevName", values="tot", aggfunc="sum")
pivot = pivot.reindex(area_order)[dev_order]
pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(9.5, 5.5))
bottom = np.zeros(len(area_order))
for d in dev_order:
    vals = pct[d].values
    ax.bar([AREA_CN[a] for a in area_order], vals, bottom=bottom, label=DEV_CN[d], width=0.6)
    for i, v in enumerate(vals):
        if v > 2:
            ax.text(i, bottom[i] + v / 2, f"{v:.1f}%", ha="center", va="center", fontsize=9, color="white")
    bottom += vals
ax.set_ylim(0, 100)
ax.set_ylabel("占比（%）")
ax.set_title("加拿大移民来源大洲 × 发展地区 堆积百分比柱状图")
ax.legend(title="发展地区", loc="upper right")
fig.tight_layout()
save(fig, "实验一_任务4_堆积百分比柱状图.png")

# 旭日图（双层同心环）
inner_vals = [area_sum[a] for a in area_order]
outer_vals, outer_labels = [], []
for a in area_order:
    for d in dev_order:
        v = pivot.loc[a, d]
        if v > 0:
            outer_vals.append(v)
            outer_labels.append(f"{AREA_CN[a]}·{DEV_CN[d]}")
area_colors = plt.cm.tab10(np.linspace(0, 1, len(area_order)))
outer_colors = []
for i, a in enumerate(area_order):
    for d in dev_order:
        if pivot.loc[a, d] > 0:
            shade = 0.75 if d == "Developed regions" else 0.45
            outer_colors.append(area_colors[i] * shade)
fig, ax = plt.subplots(figsize=(9.5, 9.5))
ax.pie(inner_vals, radius=0.62, labels=[AREA_CN[a] for a in area_order],
       colors=area_colors, labeldistance=0.38,
       wedgeprops=dict(width=0.34, edgecolor="white"))
ax.pie(outer_vals, radius=1.0, labels=outer_labels, colors=outer_colors,
       labeldistance=1.06, rotatelabels=False,
       wedgeprops=dict(width=0.34, edgecolor="white"))
ax.set_title("加拿大移民来源大洲 × 发展地区 旭日图")
fig.tight_layout()
save(fig, "实验一_任务4_旭日图.png")

# ============ 实验一 任务5 对比 ============
au, ay = load_australia()
au["tot"] = au[ay].sum(axis=1)
ca_yearly = ca[years].sum(axis=0)
au_yearly = au[ay].sum(axis=0)

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(years, ca_yearly.values, marker="o", label="加拿大（国籍口径）", color="#d62728")
ax.plot(years, au_yearly.values, marker="s", label="澳大利亚（居住地口径）", color="#1f77b4")
ax.set_title("加拿大 vs 澳大利亚 1980-2013 年移民流入总量趋势")
ax.set_xlabel("年份")
ax.set_ylabel("移民人数（人）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(kfmt))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
save(fig, "实验一_任务5_两国移民趋势对比.png")

ca_area_pct = ca.groupby("AreaName")["tot"].sum().reindex(area_order)
au_area_pct = au.groupby("AreaName")["tot"].sum().reindex(area_order)
ca_area_pct = ca_area_pct / ca_area_pct.sum() * 100
au_area_pct = au_area_pct / au_area_pct.sum() * 100

fig, ax = plt.subplots(figsize=(10.5, 5.5))
xx = np.arange(len(area_order))
ax.bar(xx - 0.2, ca_area_pct.values, 0.38, label="加拿大", color="#d62728")
ax.bar(xx + 0.2, au_area_pct.values, 0.38, label="澳大利亚", color="#1f77b4")
ax.set_xticks(xx)
ax.set_xticklabels([AREA_CN[a] for a in area_order])
ax.set_ylabel("占比（%）")
ax.set_title("加拿大 vs 澳大利亚 移民来源大洲构成对比")
ax.legend()
fig.tight_layout()
save(fig, "实验一_任务5_两国大洲构成对比.png")

# 打印关键数字供报告引用
print("=== 关键统计 ===")
print("加拿大移民总量:", int(ca["tot"].sum()))
print("前5国:", [(cn(n), int(v)) for n, v in zip(top5["OdName"], top5["tot"])])
print("大洲累计:", {AREA_CN[a]: int(v) for a, v in area_sum.items()})
print("发展地区累计:", {DEV_CN[d]: int(v) for d, v in dev_sum.items()})
print("澳大利亚移民总量:", int(au["tot"].sum()))
print("=== done ===")