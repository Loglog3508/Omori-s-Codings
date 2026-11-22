# -*- coding: utf-8 -*-
"""
第三章 二、四个 AR 模型的 ACF 图与 PACF 图

模型（e_t 为白噪声）：
    X1: x_t = 0.8 x_{t-1} + e_t
    X2: x_t = -0.8 x_{t-1} + e_t
    X3: x_t = x_{t-1} - 0.5 x_{t-2} + e_t
    X4: x_t = -x_{t-1} - 0.5 x_{t-2} + e_t

题目要求：用 for 循环生成上述四个序列，画出时序图、ACF 图与 PACF 图，
观察 ACF、PACF 的拖尾/截尾特征。

运行：python 2_AR模型.py
      图片保存在 图/ 目录；设置环境变量 HW_SHOW=1 时同时弹窗显示。
"""

import os

import numpy as np
import pandas as pd

import matplotlib
if os.environ.get("HW_SHOW", "0") != "1":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import acf, pacf

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11          # 图插入 Word 后字号不至于过小

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "图")
os.makedirs(FIG, exist_ok=True)

# ----------------------------------------------------------------------
# 1. 生成数据（n = 100，与老师给的代码一致）
# ----------------------------------------------------------------------
np.random.seed(20261120)
N = 100
X = np.zeros((N, 4))
e = np.random.normal(size=N)

for i in range(N - 1):                       # AR(1)
    X[i + 1, 0] = 0.8 * X[i, 0] + e[i]
    X[i + 1, 1] = -0.8 * X[i, 1] + e[i]

for i in range(N - 2):                       # AR(2)
    X[i + 2, 2] = X[i + 1, 2] - 0.5 * X[i, 2] + e[i]
    X[i + 2, 3] = -X[i + 1, 3] - 0.5 * X[i, 3] + e[i]

df = pd.DataFrame(X, columns=["X1", "X2", "X3", "X4"])
columns = list(df.columns)
model_names = {
    "X1": "X1:  φ1 = 0.8",
    "X2": "X2:  φ1 = -0.8",
    "X3": "X3:  φ1 = 1, φ2 = -0.5",
    "X4": "X4:  φ1 = -1, φ2 = -0.5",
}

# ----------------------------------------------------------------------
# 2. 四个模型的时序图
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.4))
for k, (ax, col) in enumerate(zip(axes.flat, columns)):
    ax.plot(np.arange(1, N + 1), df[col], color="tab:blue", linewidth=0.9)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title(model_names[col], fontsize=11)
    ax.set_xlabel("t")
    ax.set_ylabel("x")
    ax.grid(alpha=0.3)
fig.suptitle("四个 AR 模型的时序图（n = 100）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "AR四模型_时序图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 3. 四个模型的 ACF 图
# ----------------------------------------------------------------------
CI = 2 / np.sqrt(N)          # 2 倍标准误，近似 95% 置信界限
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, columns):
    plot_acf(df[col], lags=20, ax=ax, title=model_names[col], alpha=None)
    ax.axhline(CI, color="red", linestyle="--", linewidth=0.8)
    ax.axhline(-CI, color="red", linestyle="--", linewidth=0.8)
    ax.set_xlabel("延迟 k")
    ax.grid(alpha=0.3)
fig.suptitle("四个 AR 模型的样本自相关图（ACF）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "AR四模型_ACF图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 4. 四个模型的 PACF 图
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, columns):
    plot_pacf(df[col], lags=20, ax=ax, method="ywm", title=model_names[col], alpha=None)
    ax.axhline(CI, color="red", linestyle="--", linewidth=0.8)
    ax.axhline(-CI, color="red", linestyle="--", linewidth=0.8)
    ax.set_xlabel("延迟 k")
    ax.grid(alpha=0.3)
fig.suptitle("四个 AR 模型的样本偏自相关图（PACF）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "AR四模型_PACF图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 5. 输出前 6 阶样本 ACF 与 PACF，便于报告中列表比较
# ----------------------------------------------------------------------
acf_tab = pd.DataFrame(
    {col: np.round(acf(df[col], nlags=6, fft=False), 3) for col in columns},
    index=[f"k={k}" for k in range(7)],
)
pacf_tab = pd.DataFrame(
    {col: np.round(pacf(df[col], nlags=6, method="ywm"), 3) for col in columns},
    index=[f"k={k}" for k in range(7)],
)
print("=" * 60)
print("表 1  四个 AR 模型的样本自相关系数 ACF（前 6 阶）")
print(acf_tab.to_string())
print()
print("表 2  四个 AR 模型的样本偏自相关系数 PACF（前 6 阶）")
print(pacf_tab.to_string())
print()
print("n = %d，2/sqrt(n) = %.3f（ACF/PACF 的 2 倍标准误近似）" % (N, 2 / np.sqrt(N)))
print("图片已保存到：", FIG)
