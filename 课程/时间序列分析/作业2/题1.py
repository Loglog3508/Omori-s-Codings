# -*- coding: utf-8 -*-
"""习题 2-1：序列 {1, 2, 3, ..., 20}

(1) 判断该序列是否平稳；
(2) 计算前 6 阶样本自相关系数；
(3) 绘制样本自相关图，并描述该图形特征。

运行说明：脚本会把图保存到 作业2/图/ 下；默认同时弹窗显示，
若只想出图不弹窗（例如后台批处理），先设置环境变量 HW_SHOW=0。
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")          # 必须在 import pyplot 之前
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf

作业目录 = Path(__file__).resolve().parent
图目录 = 作业目录 / "图"
图目录.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- 构造序列
# 序列本身没有外部数据文件：x_t = t，t = 1, 2, ..., 20
x = pd.Series(np.arange(1, 21), index=pd.Index(range(1, 21), name="t"), name="x")
print("序列长度 n =", len(x))
print(x.to_string())

# ---------------------------------------------------------------- (1) 平稳性
# 图检验：看时序图有没有趋势、周期，波动幅度是否恒定
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(x.index, x.values, marker="o", color="#4472C4")
ax.set_xlabel("t")
ax.set_ylabel("x_t")
ax.set_title("图1-1  序列 {1,2,…,20} 的时序图")
fig.savefig(图目录 / "题1_时序图.png", dpi=150, bbox_inches="tight")
print("图1-1 已保存：图/题1_时序图.png")

# ---------------------------------------------------------------- (2) 前6阶自相关系数
r = acf(x, nlags=6, fft=False)          # 下标 0 对应延迟 0 阶（恒为 1）
print("\n前 6 阶样本自相关系数 r_k（k = 0..6）：")
for k, v in enumerate(r):
    print("  r_%d = %.6f" % (k, v))
print("  各阶相关系数：" + ", ".join("%.6f" % v for v in r[1:]))

# ---------------------------------------------------------------- (3) 自相关图
fig2 = plot_acf(x, lags=12, title="图1-2  序列 {1,2,…,20} 的样本自相关图")
fig2.set_size_inches(7, 4)
fig2.savefig(图目录 / "题1_自相关图.png", dpi=150, bbox_inches="tight")
print("图1-2 已保存：图/题1_自相关图.png")

# ---------------------------------------------------------------- 结论
print("""
结论：
(1) 非平稳。时序图上有明显的线性递增趋势，均值随 t 变化（不是常数），
    不满足平稳序列"均值为常数"的要求。
(2) 前 6 阶样本自相关系数为 1, 0.85, 0.7015, 0.5560, 0.4150, 0.2801, 0.1526，
    随延迟阶数增大而缓慢衰减。
(3) 样本自相关图呈"从 1 开始缓慢线性下降、衰减很慢"的形态，且始终为正，
    这是具有单调趋势的非平稳序列的典型自相关特征，与 (1) 的判断一致。
""")

if os.environ.get("HW_SHOW", "1") != "0":
    plt.show()
