# -*- coding: utf-8 -*-
"""习题 2-6：1969 年 1 月开始芝加哥海德公园每 28 天发生的抢包案件数（表 2-6）

(1) 判断该序列 {x_t} 的平稳性及纯随机性；
(2) 对 {x_t} 进行 1 阶差分运算 y_t = x_t - x_{t-1}，并判断 {y_t} 的平稳性及纯随机性。
    —— 按老师要求：若 x_t 已判定为非平稳序列，(2) 的一阶差分部分不做。

数据文件：课程资料1/习题数据/E2_6.xlsx（单列 x，共 70 条记录，每 28 天一条，无时间列，
故按 1969-01-01 起、间隔 28 天生成时间索引）
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
df = pd.read_excel(资料目录 / "习题数据" / "E2_6.xlsx")
df.index = pd.date_range("1969-01-01", periods=len(df), freq="28D")
print("观测数：", len(df), " 时间范围：", df.index[0].date(), "~", df.index[-1].date())

x = df["x"]
print(x.head().to_string())

# ------------------------------------------------ (1) 时序图 + 自相关图 + LB 检验
fig, axes = plt.subplots(2, 1, figsize=(9, 7))
x.plot(ax=axes[0], ylabel="x", color="#70AD47")
axes[0].set_xlabel("时间（每 28 天一期）")
axes[0].set_title("图6-1  每 28 天抢包案件数时序图（1969 年起）")

r = acf(x, nlags=24, fft=False)
axes[1].stem(list(range(len(r))), list(r), basefmt=" ")
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].set_xlabel("延迟 k")
axes[1].set_ylabel("自相关系数")
axes[1].set_title("图6-2  抢包案件数序列样本自相关图")
fig.tight_layout()
fig.savefig(图目录 / "题6_时序图与自相关图.png", dpi=150, bbox_inches="tight")
print("图6-1、图6-2 已保存：图/题6_时序图与自相关图.png")

print("\n前 24 阶样本自相关系数：")
for k, v in enumerate(r):
    print("  r_%2d = % .6f" % (k, v))

print("\n纯随机性检验（LB 统计量，延迟 1~10 阶）：")
lb = LB_test(x)
print(lb.to_string())

print("""
结论：
(1) x_t 为非平稳、非白噪声序列。
    平稳性：时序图前期均值约 15、后期均值约 12，整体存在缓慢下降的变化，
    且波动幅度不恒定，均值不是常数，图检验判为非平稳序列。
    纯随机性：延迟 1~10 阶 LB 统计量的 P 值均远小于 0.05，拒绝白噪声原假设，
    故 x_t 是非白噪声序列（自相关图滞后 1 阶相关系数约 0.51 也说明有显著相关）。
(2) 按老师要求：x_t 已判定为非平稳序列，一阶差分 y_t = x_t - x_{t-1} 部分不做。
    （如需补充，取消下方注释即可运行。）
""")

# 如需补做 (2)：
# y = x.diff(1).dropna()
# print(y.head().to_string())
# plot_acf(y, lags=24, title="图6-3  一阶差分序列样本自相关图").savefig(图目录 / "题6_差分自相关图.png", dpi=150)
# print(LB_test(y).to_string())

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
