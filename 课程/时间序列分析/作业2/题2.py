# -*- coding: utf-8 -*-
"""习题 2-2：1975—1980 年夏威夷岛莫纳罗亚火山每月释放的 CO2 数据（表 2-3）

(1) 绘制时序图，并用图检验方法判断序列是否平稳；
(2) 计算前 24 阶样本自相关系数；
(3) 绘制样本自相关图，并描述该图形的特征。

数据文件：课程资料1/习题数据/E2_2.xlsx（两列：time, co2，共 72 条月度记录）
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf

作业目录 = Path(__file__).resolve().parent
资料目录 = 作业目录.parent / "课程资料1"
图目录 = 作业目录 / "图"
图目录.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------ 读数据并设置时间索引
df = pd.read_excel(资料目录 / "习题数据" / "E2_2.xlsx", parse_dates=True, index_col=0)
df.index = df.index.to_period("M")          # 时间戳 -> 月度周期
print("索引类型：", type(df.index).__name__, " 频率：", df.index.freq, " 观测数：", len(df))
print(df.head().to_string())

co2 = df["co2"]

# ------------------------------------------------ (1) 时序图 + 图检验
fig, ax = plt.subplots(figsize=(9, 4.5))
co2.plot(ax=ax, ylabel="co2", color="#4472C4")
ax.set_xlabel("时间（月）")
ax.set_title("图2-1  CO2 月度释放量时序图（1975—1980）")
fig.savefig(图目录 / "题2_时序图.png", dpi=150, bbox_inches="tight")
print("图2-1 已保存：图/题2_时序图.png")

# ------------------------------------------------ (2) 前 24 阶自相关系数
r = acf(co2, nlags=24, fft=False)
print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

# ------------------------------------------------ (3) 自相关图
fig2 = plot_acf(co2, lags=24, title="图2-2  CO2 序列样本自相关图（延迟 24 阶）")
fig2.set_size_inches(9, 4.5)
fig2.savefig(图目录 / "题2_自相关图.png", dpi=150, bbox_inches="tight")
print("图2-2 已保存：图/题2_自相关图.png")

print("""
结论与图形特征：
(1) 非平稳。时序图上既有逐年缓慢上升的长期趋势（均值由约 331 升到约 337），
    又有明显的 12 个月周期波动，均值不是常数，故不是平稳序列。
(2) 自相关系数衰减很慢：r_1 = 0.9075、r_2 = 0.7217、r_3 = 0.5125，
    到 r_24 仍有约 0.25 的正相关，是趋势序列的典型表现。
(3) 自相关图从 1 开始缓慢衰减，并在衰减过程中叠加周期性的"波浪"起伏
    （延迟 6、12、18、24 阶附近出现局部高点），即呈现
    "长期趋势 + 季节周期并存"的特征，与 (1) 的判断一致。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
