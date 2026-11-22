# -*- coding: utf-8 -*-
"""
第三章 三、四个 MA 模型的 ACF 图与 PACF 图

模型（e_t 为白噪声）：
    X1: x_t = e_t - 2 e_{t-1}
    X2: x_t = e_t - 0.5 e_{t-1}
    X3: x_t = e_t - (4/5) e_{t-1} + (16/25) e_{t-2}
    X4: x_t = e_t - (5/4) e_{t-1} + (25/16) e_{t-2}

题目要求：自行编写代码，画出四个 MA 模型的时序图、ACF 图与 PACF 图，
观察 ACF、PACF 的拖尾/截尾特征。

说明：MA(q) 模型 x_t = e_t + θ1 e_{t-1} + ... + θq e_{t-q}，
      生成时取 e 长度为 N + q，用 e[t + q] 作为 t 时刻的 e_t。

运行：python 3_MA模型.py
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
# 1. 生成数据（n = 100）
# ----------------------------------------------------------------------
np.random.seed(2024)
N = 100
E = np.random.normal(size=N + 2)          # 多生成两项供 MA(2) 使用

theta = [(-2.0, 0.0), (-0.5, 0.0), (-0.8, 0.64), (-1.25, 1.5625)]
X = np.zeros((N, 4))
for j, (t1, t2) in enumerate(theta):
    for t in range(N):
        X[t, j] = E[t + 2] + t1 * E[t + 1] + t2 * E[t]

df = pd.DataFrame(X, columns=["X1", "X2", "X3", "X4"])
columns = list(df.columns)
model_names = {
    "X1": "X1:  θ1 = -2",
    "X2": "X2:  θ1 = -0.5",
    "X3": "X3:  θ1 = -0.8, θ2 = 0.64",
    "X4": "X4:  θ1 = -1.25, θ2 = 1.5625",
}

# ----------------------------------------------------------------------
# 2. 四个模型的时序图
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.4))
for ax, col in zip(axes.flat, columns):
    ax.plot(np.arange(1, N + 1), df[col], color="tab:orange", linewidth=0.9)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_title(model_names[col], fontsize=11)
    ax.set_xlabel("t")
    ax.set_ylabel("x")
    ax.grid(alpha=0.3)
fig.suptitle("四个 MA 模型的时序图（n = 100）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "MA四模型_时序图.png"), dpi=200)
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
fig.suptitle("四个 MA 模型的样本自相关图（ACF）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "MA四模型_ACF图.png"), dpi=200)
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
fig.suptitle("四个 MA 模型的样本偏自相关图（PACF）", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "MA四模型_PACF图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 5. 输出前 6 阶样本 ACF 与 PACF，以及理论值
# ----------------------------------------------------------------------
acf_tab = pd.DataFrame(
    {col: np.round(acf(df[col], nlags=6, fft=False), 3) for col in columns},
    index=[f"k={k}" for k in range(7)],
)
pacf_tab = pd.DataFrame(
    {col: np.round(pacf(df[col], nlags=6, method="ywm"), 3) for col in columns},
    index=[f"k={k}" for k in range(7)],
)

# 理论 ACF：rho_k = (theta_k + theta_(k+1) theta_1 + ...) / (1 + theta_1^2 + ...)，k >= 1
def theoretical_acf(t1, t2):
    denom = 1 + t1 ** 2 + t2 ** 2
    r1 = t1 * (1 + t2) / denom
    r2 = t2 / denom
    return [1.0, r1, r2] + [0.0] * 4

print("=" * 60)
print("表 1  四个 MA 模型的样本自相关系数 ACF（前 6 阶）")
print(acf_tab.to_string())
print()
print("表 2  四个 MA 模型的样本偏自相关系数 PACF（前 6 阶）")
print(pacf_tab.to_string())
print()
print("表 3  四个 MA 模型的理论 ACF（前 3 阶）")
for j, (t1, t2) in enumerate(theta):
    print("X%d:" % (j + 1), np.round(theoretical_acf(t1, t2)[:3], 4))
print()
print("n = %d，2/sqrt(n) = %.3f" % (N, 2 / np.sqrt(N)))
print("图片已保存到：", FIG)
