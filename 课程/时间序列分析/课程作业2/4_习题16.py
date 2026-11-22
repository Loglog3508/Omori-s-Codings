# -*- coding: utf-8 -*-
"""
第三章 四、课后习题 16（澳大利亚枪支凶杀案死亡率，1915—2004）

题目：
    (1) 绘制该序列的时序图，直观考察该序列的平稳特征；
    (2) 判断该序列的自相关系数与偏自相关系数的截尾或拖尾特征。

数据：课程资料1/习题数据/E2_7.xlsx（year, mortality，共 90 年）
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
# 1. 读入数据并设置年度时间索引
# ----------------------------------------------------------------------
data = pd.read_excel(os.path.join(BASE, "..", "课程资料1", "习题数据", "E2_7.xlsx"))
data["year"] = data["year"].astype(int)
data.index = pd.PeriodIndex(data["year"], freq="Y")
x = data["mortality"].astype(float)
n = len(x)

# ----------------------------------------------------------------------
# 2. 时序图
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.0, 3.0))
ax.plot(data.index.astype(str), x.values, color="tab:blue", linewidth=1.2)
ax.set_xlabel("年份")
ax.set_ylabel("死亡率（每 10 万人）")
ax.set_title("1915—2004 年澳大利亚枪支凶杀案死亡率时序图")
ax.grid(alpha=0.3)
step = 10
ax.set_xticks([str(y) for y in data["year"].values[::step]])
fig.tight_layout()
fig.savefig(os.path.join(FIG, "习题16_时序图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 3. ACF 图与 PACF 图（延迟 24 期）
# ----------------------------------------------------------------------
CI = 2 / np.sqrt(n)          # 2 倍标准误，近似 95% 置信界限
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1))
plot_acf(x, lags=24, ax=axes[0], title="mortality 的自相关图（ACF）", alpha=None)
axes[0].axhline(CI, color="red", linestyle="--", linewidth=0.8)
axes[0].axhline(-CI, color="red", linestyle="--", linewidth=0.8)
axes[0].set_xlabel("延迟 k")
axes[0].grid(alpha=0.3)
plot_pacf(x, lags=24, ax=axes[1], method="ywm", title="mortality 的偏自相关图（PACF）", alpha=None)
axes[1].axhline(CI, color="red", linestyle="--", linewidth=0.8)
axes[1].axhline(-CI, color="red", linestyle="--", linewidth=0.8)
axes[1].set_xlabel("延迟 k")
axes[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "习题16_ACF与PACF图.png"), dpi=200)
plt.close(fig)

# ----------------------------------------------------------------------
# 4. 输出统计量与相关系数
# ----------------------------------------------------------------------
a = acf(x, nlags=24, fft=False)
p = pacf(x, nlags=24, method="ywm")

print("=" * 60)
print("习题 16：澳大利亚枪支凶杀案死亡率（1915—2004，n = %d）" % n)
print("均值 = %.4f，标准差 = %.4f，最小值 = %.4f，最大值 = %.4f"
      % (x.mean(), x.std(), x.min(), x.max()))
print()
print("样本自相关系数 ACF（k = 1~12）：")
print("  ", np.round(a[1:13], 3))
print("样本偏自相关系数 PACF（k = 1~12）：")
print("  ", np.round(p[1:13], 3))
print()
print("2/sqrt(n) = %.3f" % (2 / np.sqrt(n)))
print("图片已保存到：", FIG)
