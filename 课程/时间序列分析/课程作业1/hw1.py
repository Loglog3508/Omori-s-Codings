# -*- coding: utf-8 -*-
"""
课程作业1 —— 案例数据 A1_7：每年地震次数（1900-1998）

参考课程代码：
    file7 = pd.read_excel("...A1_7.xlsx", parse_dates=True, index_col=0)  # 第一列设为时间索引
    file7 = file7.to_period()      # 时间戳 -> 时间段（周期）
    file7.number.plot(ylabel="number")
    plot_acf(file7.number).show()
    LB_test(file7.number)
"""
# ---------- 导入分析工具（与课程 env.py 一致，顺序已修正） ----------
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

DATA = r"C:\Users\omori\Omori-s-Codings\课程\时间序列分析\课程资料1\案例数据\A1_7.xlsx"
OUT = r"C:\Users\omori\Omori-s-Codings\课程\时间序列分析\课程作业1"

# ---------- 1. 读取数据，第一列设为时间索引 ----------
file7 = pd.read_excel(DATA, parse_dates=True, index_col=0)
# ---------- 2. 精确时间点（时间戳）→ 时间段（周期） ----------
file7 = file7.to_period()

print("索引类型 :", type(file7.index).__name__, "| 频率:", file7.index.freqstr)
print(file7.head())
print("样本量   :", len(file7))

# ---------- 3. 时序图 ----------
ax = file7["number"].plot(ylabel="number", title="A1_7 每年地震次数（1900-1998）")
ax.figure.tight_layout()
ax.figure.savefig(OUT + r"\A1_7_series.png", dpi=150)

# ---------- 4. ACF 图 ----------
fig = plot_acf(file7["number"])
fig.tight_layout()
fig.savefig(OUT + r"\A1_7_acf.png", dpi=150)

# ---------- 5. Ljung-Box 白噪声检验 ----------
lb = LB_test(file7["number"], return_df=True)
print("\nLjung-Box 检验（滞后 1~10 阶）：")
print(lb)

plt.show()
