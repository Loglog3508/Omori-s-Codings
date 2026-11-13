# -*- coding: utf-8 -*-
"""习题 2-5：某公司 2000—2003 年每月销售量（表 2-5）

(1) 绘制该序列的时序图及样本自相关图；
(2) 使用图检验方法，判断该序列的平稳性；
(3) 判断该序列的纯随机性。

数据文件：课程资料1/习题数据/E2_5.xlsx（两列：time, x，共 48 条月度记录）
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox as LB_test

作业目录 = Path(__file__).resolve().parent
资料目录 = 作业目录.parent / "课程资料1"
图目录 = 作业目录 / "图"
图目录.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------ 读数据并设置时间索引
df = pd.read_excel(资料目录 / "习题数据" / "E2_5.xlsx", parse_dates=True, index_col=0)
df.index = df.index.to_period("M")
print("索引类型：", type(df.index).__name__, " 频率：", df.index.freq, " 观测数：", len(df))
print(df.head().to_string())

x = df["x"]

# ------------------------------------------------ (1) 时序图 + 样本自相关图
fig, axes = plt.subplots(2, 1, figsize=(9, 7))
x.plot(ax=axes[0], ylabel="x", color="#4472C4")
axes[0].set_xlabel("时间（月）")
axes[0].set_title("图5-1  月度销售量时序图（2000—2003）")

from statsmodels.tsa.stattools import acf
r = acf(x, nlags=24, fft=False)
lags = range(len(r))
axes[1].stem(list(lags), list(r), basefmt=" ")
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set_xlabel("延迟 k")
axes[1].set_ylabel("自相关系数")
axes[1].set_title("图5-2  月度销售量序列样本自相关图")

fig.tight_layout()
fig.savefig(图目录 / "题5_时序图与自相关图.png", dpi=150, bbox_inches="tight")
print("图5-1、图5-2 已保存：图/题5_时序图与自相关图.png")

print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

# ------------------------------------------------ (2) 图检验：平稳性
print("""
(2) 平稳性判断：非平稳。
    时序图呈明显的"锯齿状"季节波动，同时每年的整体水平逐年下降
    （2000 年峰值 300 左右 → 2003 年峰值 248 左右），均值不是常数，
    图检验认为该序列非平稳。
""")

# ------------------------------------------------ (3) 纯随机性：LB 检验
print("(3) 纯随机性检验（LB 统计量，默认延迟 1~10 阶）：")
lb = LB_test(x)
print(lb.to_string())
print("""    延迟 1~10 阶的 LB 统计量 P 值均小于显著性水平 0.05，
    因此拒绝"序列为纯随机序列"的原假设，该序列为非白噪声序列。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
