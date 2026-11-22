# -*- coding: utf-8 -*-
"""
第三章 一、计算题（平稳性与可逆性检验，程序验证）

用程序求 AR 部分特征根与 MA 部分特征根，对第 11 题的 6 个模型给出
"平稳 / 非平稳" 与 "可逆 / 不可逆" 的数值判断，用于核对手算结果。

判别准则：
    AR 部分：x_t = phi_1 x_(t-1) + ... + phi_p x_(t-p) + e_t
             特征方程  lambda^p - phi_1 lambda^(p-1) - ... - phi_p = 0
             平稳 <=> 所有特征根满足 |lambda| < 1
    MA 部分：x_t = e_t + theta_1 e_(t-1) + ... + theta_q e_(t-q)
             特征方程  1 + theta_1 z + ... + theta_q z^q = 0
             可逆 <=> 所有根满足 |z| > 1

另：习题 3.(2) 中 "随机游走的一阶差分序列是平稳序列" 的数值验证。
"""

import numpy as np

# ----------------------------------------------------------------------
# 1. 第 11 题六个模型
# ----------------------------------------------------------------------
# 每个元素：(题号, AR 系数 phi_1..phi_p, MA 系数 theta_1..theta_q)
models = [
    ("(1)", [0.5, 1.2], []),
    ("(2)", [1.1, -0.3], []),
    ("(3)", [], [-0.9, 0.3]),
    ("(4)", [], [1.3, -0.4]),
    ("(5)", [0.7], [-0.6]),
    ("(6)", [-0.8, 0.5], [-1.1]),
]


def ar_roots(phi):
    """AR 特征根 lambda：lambda^p - phi_1 lambda^(p-1) - ... - phi_p = 0"""
    p = len(phi)
    coef = [1.0] + [-c for c in phi]
    return np.roots(coef)


def ma_roots(theta):
    """MA 特征根 z：1 + theta_1 z + ... + theta_q z^q = 0"""
    q = len(theta)
    coef = list(theta)[::-1] + [1.0]      # 从高次到常数项
    return np.roots(coef)


def fmt(roots):
    out = []
    for r in roots:
        if abs(r.imag) < 1e-9:
            out.append("%.4f" % r.real)
        else:
            sign = "+" if r.imag >= 0 else "-"
            out.append("%.4f%s%.4fj" % (r.real, sign, abs(r.imag)))
    return ", ".join(out)


print("=" * 78)
print("第 11 题：模型平稳性与可逆性检验")
print("=" * 78)
for tag, phi, theta in models:
    print("\n模型 %s" % tag)
    stationary = True
    if phi:
        r = ar_roots(phi)
        mods = np.abs(r)
        stationary = bool(np.all(mods < 1))
        print("  AR 特征根 lambda = %s" % fmt(r))
        print("  |lambda| = %s  -> %s" % (np.round(mods, 4), "平稳" if stationary else "非平稳"))
    else:
        print("  无 AR 部分（MA 模型）-> 平稳")

    invertible = True
    if theta:
        z = ma_roots(theta)
        mods = np.abs(z)
        invertible = bool(np.all(mods > 1))
        print("  MA 特征根 z = %s" % fmt(z))
        print("  |z| = %s  -> %s" % (np.round(mods, 4), "可逆" if invertible else "不可逆"))
    else:
        print("  无 MA 部分（AR 模型）-> 可逆")

    if stationary and invertible:
        verdict = "平稳且可逆"
    elif stationary and not invertible:
        verdict = "平稳但不可逆"
    elif (not stationary) and invertible:
        verdict = "非平稳（MA 可逆）"
    else:
        verdict = "非平稳且不可逆"
    print("  ==> 结论：%s" % verdict)

# ----------------------------------------------------------------------
# 2. 随机游走的一阶差分（对应资料中的 (2)）
# ----------------------------------------------------------------------
print()
print("=" * 78)
print("随机游走 x_t = x_(t-1) + e_t 的一阶差分 y_t = x_t - x_(t-1)")
print("=" * 78)
np.random.seed(20261120)
n = 500
e = np.random.normal(size=n)
x = np.cumsum(e)               # 随机游走，x_0 = 0
y = np.diff(x)                 # y_t = e_t

from statsmodels.tsa.stattools import acf

print("y 的均值 = %.4f，标准差 = %.4f（真值：均值 0，标准差 1）"
      % (y.mean(), y.std(ddof=1)))
print("y 的样本自相关系数（k = 0~5）：", np.round(acf(y, nlags=5, fft=False), 3))
print("理论值：rho_0 = 1，rho_k = 0（k >= 1）")
print()
print("说明：1 阶差分把随机游走还原成白噪声 e_t，白噪声是平稳序列，")
print("      且各阶自相关系数（k>=1）为 0，故 ACF 在 0 阶后截尾。")
