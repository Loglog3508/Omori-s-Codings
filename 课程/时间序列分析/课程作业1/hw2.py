# -*- coding: utf-8 -*-
"""
课程作业2 —— 按黑板上写的四步走

① 导入数据后 完成“时间索引”
② 方程 AR(p) 的时序图实现          x_t = 0.8 * x_{t-1} + e_t
③ 自相关系数图 acf 实现
④ 自相关系数的计算（按公式手算，再和 acf() 的结果对照）
"""
# ---------- 导入分析工具（与课程 env.py 一致，顺序已修正） ----------
import os
import numpy as np
import pandas as pd
import statistics
import statsmodels
import matplotlib
matplotlib.use("TkAgg")          # 必须在导入 pyplot 之前指定后端
import openpyxl
import matplotlib.pyplot as plt
from statsmodels.tsa.api import acf
from statsmodels.stats.diagnostic import acorr_ljungbox as LB_test
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.api import adfuller
from statsmodels.tsa.api import SARIMAX
from statsmodels.graphics.tsaplots import plot_predict

# 让图里的中文正常显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"C:\Users\omori\Omori-s-Codings\课程\时间序列分析\课程作业1"
DATA = os.path.join(OUT, "例3-2_AR1数据.xlsx")

# ---------- 0. 按方程 x_t = 0.8 x_{t-1} + e_t 生成数据，存成 A1_7 格式的 xlsx ----------
n = 100
rng = np.random.default_rng(2026)
eps = rng.normal(size=n)
x = np.zeros(n)
for t in range(1, n):
    x[t] = 0.8 * x[t - 1] + eps[t]

pd.DataFrame({
    "year": pd.date_range("1900-01-01", periods=n, freq="YS"),   # 第一列时间索引
    "x": x,
}).to_excel(DATA, index=False, sheet_name="AR1")

# ---------- ① 导入数据后，完成“时间索引” ----------
# 与课程读 A1_7 的写法相同：第一列设为时间索引
file = pd.read_excel(DATA, parse_dates=True, index_col=0)
file = file.to_period()          # 时间戳 → 周期
print("① 索引类型:", type(file.index).__name__, "| 频率:", file.index.freqstr)
print(file.head())

ts = file["x"]

# ---------- ② 方程 AR(p) 的时序图实现 ----------
ax = ts.plot(ylabel="x", title="AR(1) 时序图   x_t = 0.8 x_{t-1} + e_t")
ax.figure.tight_layout()
ax.figure.savefig(os.path.join(OUT, "AR1_series.png"), dpi=150)

# ---------- ③ 自相关系数图 acf 实现 ----------
fig = plot_acf(ts, lags=20, title="AR(1) 自相关图（ACF）")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "AR1_acf.png"), dpi=150)

# ---------- ④ 自相关系数的计算 ----------
# 公式： r_k = sum_{t=k+1..n} (x_t - xbar)(x_{t-k} - xbar) / sum_{t=1..n} (x_t - xbar)^2
z = ts.values - ts.values.mean()
denominator = (z ** 2).sum()

manual = []
for k in range(11):
    numerator = (z[k:] * z[:n - k]).sum()
    manual.append(numerator / denominator)        # k = 0 时为 1

auto = acf(ts.values, nlags=10, fft=False)        # statsmodels 自带的自相关系数

table = pd.DataFrame({
    "滞后 k": range(11),
    "手工计算 r_k": np.round(manual, 6),
    "acf() 结果": np.round(auto, 6),
})
print("\n④ 自相关系数（滞后 0~10 阶）：")
print(table.to_string(index=False))
print("\n手工计算与 acf() 的最大差异：%.2e" % np.abs(np.array(manual) - auto).max())

plt.show()
