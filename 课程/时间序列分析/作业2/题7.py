# -*- coding: utf-8 -*-
"""习题 2-7：1915—2004 年澳大利亚每年与枪支有关的凶杀案死亡率（表 2-7）

(1) 绘制时序图，直观考察该序列的平稳特征；
(2) 绘制自相关图，分析该序列的平稳性；
(3) 如果是平稳序列，分析纯随机性；如果是非平稳序列，分析一阶差分后序列的平稳性。
    —— 按老师要求：本题序列判定为非平稳，(3) 中的一阶差分部分不做。

数据文件：课程资料1/习题数据/E2_7.xlsx（两列：year, mortality，共 90 条年度记录）
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
df = pd.read_excel(资料目录 / "习题数据" / "E2_7.xlsx")
年份 = df.pop("year").astype(int)                                   # 取出年份列
df.index = pd.PeriodIndex(年份.astype(str), freq="Y")               # 年度周期索引
df.index.name = "年份"
print("索引类型：", type(df.index).__name__, " 频率：", df.index.freq,
      " 观测数：", len(df), " 年份：", 年份.iloc[0], "—", 年份.iloc[-1])
print(df.head().to_string())

m = df["mortality"]

# ------------------------------------------------ (1) 时序图
fig, ax = plt.subplots(figsize=(9, 4.5))
m.plot(ax=ax, ylabel="mortality", color="#C00000")
ax.set_xlabel("年份")
ax.set_title("图7-1  澳大利亚枪支凶杀案死亡率时序图（1915—2004）")
fig.savefig(图目录 / "题7_时序图.png", dpi=150, bbox_inches="tight")
print("图7-1 已保存：图/题7_时序图.png")

# ------------------------------------------------ (2) 自相关图
r = acf(m, nlags=24, fft=False)
print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

fig2 = plot_acf(m, lags=24, title="图7-2  凶杀案死亡率序列样本自相关图（延迟 24 阶）")
fig2.set_size_inches(9, 4.5)
fig2.savefig(图目录 / "题7_自相关图.png", dpi=150, bbox_inches="tight")
print("图7-2 已保存：图/题7_自相关图.png")

print("\n参考：LB 统计量（延迟 1~10 阶）")
print(LB_test(m).to_string())

print("""
结论：
(1) 非平稳。时序图显示死亡率由 1915 年前后的 0.5 左右长期下降到 2004 年的 0.16，
    存在明显的下降趋势，均值随时间变化，不满足平稳性要求。
(2) 自相关图从 1 开始缓慢衰减（r_1 = 0.5608、r_2 = 0.4620、r_3 = 0.3763 …），
    并且一直为正、衰减很慢，属于带趋势序列的典型自相关形态，进一步说明非平稳。
(3) 按老师要求：该序列为非平稳序列，(3) 中"分析一阶差分后序列的平稳性"
    这一部分不做。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
