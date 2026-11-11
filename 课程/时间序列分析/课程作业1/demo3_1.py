# -*- coding: utf-8 -*-
"""
例 3-1 时序图复现：四条示例序列 x1~x4
做法：先把数据存成和 A1_7.xlsx 同样格式的 Excel 数据文件（第一列时间、后面是数值列），
      再用课程里读 A1_7 的方式 read_excel + to_period 读进来，
      最后用一个 for 循环在 2×2 画布上画出四张图。
左列：平稳特征     右列：非平稳特征
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:\Users\omori\Omori-s-Codings\课程\时间序列分析\课程作业1"
DATA = os.path.join(OUT, "例3-1_数据.xlsx")
FIG = os.path.join(OUT, "例3-1_时序图.png")

# ---------- 1. 生成四条示例序列，存成 A1_7 格式的 xlsx ----------
n = 100
rng = np.random.default_rng(2026)

# x1、x3：平稳序列（AR(1)，|φ|<1）
x1 = np.zeros(n)
x3 = np.zeros(n)
for t in range(1, n):
    x1[t] = 0.6 * x1[t - 1] + rng.normal()
    x3[t] = 0.6 * x3[t - 1] + rng.normal()

# x2：非平稳——AR(1) 系数 φ=-1.03（|φ|>1），符号交替、振幅指数式增长
x2 = np.zeros(n)
for t in range(1, n):
    x2[t] = -1.03 * x2[t - 1] + rng.normal()
x2 = x2 / np.abs(x2).max() * 35000     # 只缩放幅值，和课件图的量级对齐

# x4：非平稳——确定性趋势（前段几乎为 0，末尾急剧下降）
t = np.arange(n)
x4 = -8 * (t / (n - 1)) ** 12

df_out = pd.DataFrame({
    "year": pd.date_range("1900-01-01", periods=n, freq="YS"),   # 第一列时间索引
    "x1": x1, "x2": x2, "x3": x3, "x4": x4,
})
df_out.to_excel(DATA, index=False, sheet_name="例3-1")

# ---------- 2. 按读 A1_7 的方式读数据 ----------
# file7 = pd.read_excel("C:\\案例数据\\A1_7.xlsx", parse_dates=True, index_col=0)
file31 = pd.read_excel(DATA, parse_dates=True, index_col=0)
file31 = file31.to_period()            # 时间戳 → 周期
print(file31.head())

# ---------- 3. for 循环画 2×2 四张图 ----------
x = np.arange(len(file31))
colors = ["#4472C4", "#ED7D31", "#70AD47", "#C00000"]   # 蓝、橙、绿、红

fig, axes = plt.subplots(2, 2, figsize=(9, 8))
for (name, s), ax, color in zip(file31.items(), axes.flat, colors):
    ax.plot(x, s.values, color=color, linewidth=1.2, label=name)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xlim(0, n - 1)
    ax.set_xticks(range(0, n, 20))
    ax.tick_params(labelsize=8)

# 左右两列的文字说明（与课件一致）
fig.text(0.035, 0.5, "平\n稳\n特\n征", fontsize=15, va="center", ha="center")
fig.text(0.965, 0.5, "非\n平\n稳\n特\n征", fontsize=15, va="center", ha="center")
fig.suptitle("例3-1 时序图", fontsize=16)

fig.tight_layout(rect=[0.08, 0.0, 0.92, 0.96])
fig.savefig(FIG, dpi=150)

plt.show()
