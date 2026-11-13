# -*- coding: utf-8 -*-
"""习题 2-3：1945—1950 年费城月度降雨量数据（表 2-4）

(1) 绘制时序图，并用图检验方法判断序列是否平稳；
(2) 计算前 24 阶样本自相关系数；
(3) 绘制样本自相关图，并描述该图形的特征。

数据文件：课程资料1/习题数据/E2_3.xlsx（两列：time, rain，共 72 条月度记录）
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
df = pd.read_excel(资料目录 / "习题数据" / "E2_3.xlsx", parse_dates=True, index_col=0)
df.index = df.index.to_period("M")
print("索引类型：", type(df.index).__name__, " 频率：", df.index.freq, " 观测数：", len(df))
print(df.head().to_string())

rain = df["rain"]

# ------------------------------------------------ (1) 时序图 + 图检验
fig, ax = plt.subplots(figsize=(9, 4.5))
rain.plot(ax=ax, ylabel="rain", color="#ED7D31")
ax.set_xlabel("时间（月）")
ax.set_title("图3-1  费城月度降雨量时序图（1945—1950）")
fig.savefig(图目录 / "题3_时序图.png", dpi=150, bbox_inches="tight")
print("图3-1 已保存：图/题3_时序图.png")

# ------------------------------------------------ (2) 前 24 阶自相关系数
r = acf(rain, nlags=24, fft=False)
print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

# ------------------------------------------------ (3) 自相关图
fig2 = plot_acf(rain, lags=24, title="图3-2  降雨量序列样本自相关图（延迟 24 阶）")
fig2.set_size_inches(9, 4.5)
fig2.savefig(图目录 / "题3_自相关图.png", dpi=150, bbox_inches="tight")
print("图3-2 已保存：图/题3_自相关图.png")

print("""
结论与图形特征：
(1) 平稳。时序图围绕同一水平（均值约 95 mm）上下波动，没有明显的上升/下降趋势，
    波动幅度也基本保持一致，图检验认为序列平稳。
(2) 自相关系数 r_1 = 0.0128、r_2 = 0.0416、r_3 = -0.0432、r_4 = -0.1787、
    r_5 = -0.2513 …… 数值都在 0 附近来回摆动，没有缓慢衰减的趋势。
(3) 自相关图呈现明显的三角函数式波动规律：相关系数正负交替、每隔若干阶
    出现一次峰谷（约在延迟 11~12 阶、21~22 阶出现正高峰），
    这是序列存在 12 个月季节性的表现，而整体水平不升不降说明序列平稳。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
