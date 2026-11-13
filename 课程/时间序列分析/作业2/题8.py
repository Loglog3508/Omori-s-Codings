# -*- coding: utf-8 -*-
"""习题 2-8：1860—1955 年密歇根湖每月平均水位的最高值序列（表 2-8）

(1) 绘制时序图，直观考察该序列的平稳特征；
(2) 绘制自相关图，分析该序列的平稳性；
(3) 如果是平稳序列，分析纯随机性；如果是非平稳序列，分析一阶差分后序列的平稳性。
    —— 按老师要求：本题序列判定为非平稳，(3) 中的一阶差分部分不做。

数据文件：课程资料1/习题数据/E2_8.xlsx（两列：year, wl，共 96 条年度记录）
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox as LB_test

作业目录 = Path(__file__).resolve().parent
资料目录 = 作业目录.parent / "课程资料1"
图目录 = 作业目录 / "图"
图目录.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------ 读数据并设置时间索引
df = pd.read_excel(资料目录 / "习题数据" / "E2_8.xlsx")
年份 = df.pop("year").astype(int)
df.index = pd.PeriodIndex(年份.astype(str), freq="Y")
df.index.name = "年份"
print("索引类型：", type(df.index).__name__, " 频率：", df.index.freq,
      " 观测数：", len(df), " 年份：", 年份.iloc[0], "—", 年份.iloc[-1])
print(df.head().to_string())

wl = df["wl"]

# ------------------------------------------------ (1) 时序图
fig, ax = plt.subplots(figsize=(9, 4.5))
wl.plot(ax=ax, ylabel="wl", color="#4472C4")
ax.set_xlabel("年份")
ax.set_title("图8-1  密歇根湖年度最高水位序列时序图（1860—1955）")
fig.savefig(图目录 / "题8_时序图.png", dpi=150, bbox_inches="tight")
print("图8-1 已保存：图/题8_时序图.png")

# ------------------------------------------------ (2) 自相关图
r = acf(wl, nlags=24, fft=False)
print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

fig2 = plot_acf(wl, lags=24, title="图8-2  湖面水位序列样本自相关图（延迟 24 阶）")
fig2.set_size_inches(9, 4.5)
fig2.savefig(图目录 / "题8_自相关图.png", dpi=150, bbox_inches="tight")
print("图8-2 已保存：图/题8_自相关图.png")

print("\n参考：LB 统计量（延迟 1~10 阶）")
print(LB_test(wl).to_string())

print("""
结论：
(1) 非平稳。时序图显示水位在 81~84 之间做长周期起伏（约 20~30 年的涨落），
    周期长度与样本长度相当、振幅基本不变，看不出回到固定均值的趋势，
    图检验判为非平稳序列。
(2) 自相关图从 1 开始缓慢、几乎线性地衰减（r_1 = 0.8503、r_2 = 0.6668、
    r_3 = 0.5523 …，到延迟 24 阶仍有约 0.2），衰减远慢于平稳序列应有的速度，
    属于典型的非平稳（含长周期成分）序列特征。
(3) 按老师要求：该序列为非平稳序列，(3) 中"分析一阶差分后序列的平稳性"
    这一部分不做。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
