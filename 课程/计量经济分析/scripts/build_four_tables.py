# -*- coding: utf-8 -*-
"""
计量经济分析 · 第四章「函数形式与虚拟变量」—— 四个表 + 数据分析

数据口径（重要）
  · 主分析：2017cmds20%子样本_处理后.dta（N=14,836），只用其【原始问卷变量 + 城市编码】。
  · 城市人口：landscan2017城市总人口.dta，按【省代码 + 市代码】匹配到每个流动人口样本，
    得到“城市总人口”（人口栅格汇总 SUM），取对数生成 lnpop。
    这替代了原 _处理后.dta 自带的 lnpop（该变量在原始文件中按 ln(人/10000) 生成，量纲不同）。
  · 其他变量由原始问卷重建：
      lnwage   = ln(月工资 wagemonth)            [wagemonth = Q215]
      educ     = 受教育年限 eduyear（_处理后.dta 中已换算好，直接沿用）
      exp      = age − 6 − educ
      marr     = marriage（_处理后.dta 中由 q101h1 生成）
      male     = q101b1 性别
      health   = Q401 健康状况（1 健康 → 3 一般 → 2 基本健康 → 4 不健康…）
      luohu    = ??? 原始 2017 CMDS 问卷未含“落户意愿”题，故第四章例 4.5 的线性概率模型
                 改用 Q201A（五一前一周工作时间，小时）作为“因变量为定量变量”的补充；
                 虚拟变量作为因变量的 LPM 用 health 说明，见报告说明。
  · wage_chap4.dta 为另一口径（N=14,757，城市变量经过匿名化、lnpop=ln(人口/1000)），
    不作为主数据，仅在报告中作一致性对照。

表1  描述性统计（landscan 城市人口口径）
表2  城市规模对劳动者工资的影响：单变量 → 加控制 → 加行业/职业固定效应 → 加交互项
表3  函数形式对比：线性-线性 / 对数-线性 / 多项式 / 双对数 / 双对数+控制
表4  虚拟变量与交互项：分组均值 + male×marr、male×educ、lnpop×educ（4.37A / 4.37B）

输出（输出/）：
  四个表.xlsx / 四个表.docx / 数据分析报告.docx
"""
import os
from collections import OrderedDict
from math import erfc, exp, lgamma, log, sqrt

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "实验一")
OUT = os.path.join(BASE, "输出")
os.makedirs(OUT, exist_ok=True)

STARS = [(0.01, "***"), (0.05, "**"), (0.10, "*")]


# ----------------------------------------------------------------------------
# 统计工具
# ----------------------------------------------------------------------------
def _betacf(a, b, x):
    maxit, eps, fpmin = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = fpmin if abs(d) < fpmin else d
    d, h = 1.0 / d, 1.0 / d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def _ibeta(x, a, b):
    """正则化不完全贝塔函数 I_x(a,b)"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = lgamma(a + b) - lgamma(a) - lgamma(b) + a * log(x) + b * log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - exp(lbt) * _betacf(b, a, 1 - x) / b


def t_pvalue(t, df):
    if df > 200000:
        return erfc(abs(t) / sqrt(2.0))
    return _ibeta(df / (df + t * t), df / 2.0, 0.5)


def f_pvalue(F, df1, df2):
    return _ibeta(df2 / (df2 + df1 * F), df2 / 2.0, df1 / 2.0)


def ols(y, X, names):
    y, X = np.asarray(y, float), np.asarray(X, float)
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ (X.T @ y)
    e = y - X @ b
    rss = float(e @ e)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - rss / tss
    adj = 1 - (1 - r2) * (n - 1) / (n - k)
    df = n - k
    se = np.sqrt(np.diag(XtX_inv) * (rss / df))
    t = b / se
    p = np.array([t_pvalue(abs(v), df) for v in t])
    return dict(b=b, se=se, t=t, p=p, r2=r2, adj_r2=adj, n=n, df=df, rss=rss, tss=tss,
                names=list(names))


def design(df, specs):
    """specs: [(变量名, 系数表显示名)]，自动加常数项"""
    cols, names = [np.ones(len(df))], ["_cons"]
    for var, nm in specs:
        cols.append(np.asarray(df[var], dtype=float))
        names.append(nm)
    return np.column_stack(cols), names


def star(p):
    for th, s in STARS:
        if p < th:
            return s
    return ""


def coef_rows(res, order, label_map=None):
    idx = {n: i for i, n in enumerate(res["names"])}
    rows = []
    for nm in order:
        if nm not in idx:
            rows += [("", ""), ("", "")]
            continue
        i = idx[nm]
        rows.append(((label_map or {}).get(nm, nm), f"{res['b'][i]:.3f}{star(res['p'][i])}"))
        rows.append(("", f"({res['se'][i]:.3f})"))
    return rows


def _build_reg_table(results, cols, order, lab):
    rr = [coef_rows(r, order, lab) for r in results]
    # 只保留至少在一列中出现的变量，避免整行空白的变量行
    rows = []
    for nm in order:
        if not any(nm in r["names"] for r in results):
            continue
        for i in range(len(order) * 2):
            if order[i // 2] != nm:
                continue
            lab_row = rr[0][i][0]
            if i % 2 == 0 and not lab_row and len(results) > 1:
                # 取第一个包含该变量的列作为变量名来源
                for res_i, r in enumerate(results):
                    if nm in r["names"]:
                        lab_row = rr[res_i][i][0]
                        break
            rows.append([lab_row] + [rr[j][i][1] for j in range(len(results))])
    return pd.DataFrame(rows, columns=["变量"] + cols)


def build_reg_table(results, cols, order, lab, extra_rows=None):
    tab = _build_reg_table(results, cols, order, lab)
    tail = [["观测值 N"] + [f"{r['n']:,}" for r in results],
            ["R²"] + [f"{r['r2']:.3f}" for r in results],
            ["调整 R²"] + [f"{r['adj_r2']:.3f}" for r in results]]
    tail += extra_rows or []
    return pd.concat([tab, pd.DataFrame(tail, columns=["变量"] + cols)], ignore_index=True)


def nested_f(r_short, r_long):
    """r_short = 受限模型（少变量），r_long = 非受限模型（多变量）"""
    q = r_short["df"] - r_long["df"]
    F = ((r_short["rss"] - r_long["rss"]) / q) / (r_long["rss"] / r_long["df"])
    return F, q, r_long["df"], f_pvalue(F, q, r_long["df"])


def get(res, nm):
    i = res["names"].index(nm)
    return float(res["b"][i]), float(res["se"][i]), float(res["p"][i])


def pct(b):
    """对数因变量下，系数 → 精确百分比变化"""
    return 100 * (exp(b) - 1)


# ----------------------------------------------------------------------------
# 1) 数据：只用 实验一\CMDS2017子样本.dta（7 个变量，N=14,757）
#    该文件已含 male / eduyear / exp / exp2 / marriage / lnpop / lnwage
#    lnpop = ln(城市总人口/1000)，lnwage = ln(月工资)，exp2 = exp²
# ----------------------------------------------------------------------------
raw = pd.read_stata(os.path.join(DATA, "CMDS2017子样本.dta"), convert_categoricals=False)

df = pd.DataFrame()
df["male"] = raw["male"].astype(float)                    # 性别：男性=1，女性=0
df["educ"] = raw["eduyear"].astype(float)                 # 受教育年限
df["exp"] = raw["exp"].astype(float)                      # 工作经验
df["exp2"] = raw["exp2"].astype(float)                    # 工作经验平方
df["marr"] = raw["marriage"].astype(float)                # 婚姻：已婚=1
df["lnpop"] = raw["lnpop"].astype(float)                  # 城市人口规模对数
df["lnwage"] = raw["lnwage"].astype(float)                # 月工资对数

df["lnpop_x_educ"] = df["lnpop"] * df["educ"]
df["lnpop_x_male"] = df["lnpop"] * df["male"]
df["lnpop_x_marr"] = df["lnpop"] * df["marr"]
df["male_x_marr"] = df["male"] * df["marr"]
df["male_x_educ"] = df["male"] * df["educ"]
df["c_lnpop"] = df["lnpop"] - df["lnpop"].mean()           # 中心化：用于 4.37B
df["c_educ"] = df["educ"] - df["educ"].mean()
df["clnpop_x_ceduc"] = df["c_lnpop"] * df["c_educ"]
df["lnpop3"] = df["lnpop"] ** 3
df["marr_x_exp"] = df["marr"] * df["exp"]
df["male_x_exp"] = df["male"] * df["exp"]

df = df.dropna(subset=["lnwage", "lnpop", "educ", "exp", "male", "marr"]).reset_index(drop=True)
N = len(df)

FE = np.zeros((N, 0))
FE_NAMES = []

base_spec = [("lnpop", "lnpop"), ("male", "male"), ("marr", "marr"), ("educ", "educ"),
             ("exp", "exp"), ("exp2", "exp2")]
y = df["lnwage"].values

# ============================================================================
# 表 1  描述性统计
# ============================================================================
t1_vars = OrderedDict([
    ("male", "性别（男性=1，女性=0）"),
    ("educ", "受教育年限（年）"),
    ("exp", "工作经验（年）"),
    ("exp2", "工作经验平方"),
    ("marr", "婚姻（已婚=1，未婚=0）"),
    ("lnpop", "城市人口规模对数 lnpop"),
    ("lnwage", "月工资对数 lnwage"),
])
table1 = pd.DataFrame(
    [(v, lab, int(df[v].notna().sum()), round(float(df[v].mean()), 3), round(float(df[v].std(ddof=1)), 3),
      round(float(df[v].min()), 3), round(float(df[v].max()), 3)) for v, lab in t1_vars.items()],
    columns=["VarName", "变量含义", "Obs", "Mean", "SD", "Min", "Max"])

df["pop_q"] = pd.qcut(df["lnpop"], 4, labels=["Q1 最小", "Q2", "Q3", "Q4 最大"])
popq = df.groupby("pop_q", observed=True).agg(
    N=("lnwage", "size"), 城市数=("lnpop", "nunique"),
    lnpop均值=("lnpop", "mean"), lnwage均值=("lnwage", "mean"),
    educ均值=("educ", "mean")).round(3).reset_index()
popq = popq.rename(columns={"pop_q": "城市规模四分位（按 lnpop）"})

# ============================================================================
# 表 2  双变量回归 vs 多元回归（城市规模 → 工资，逐步加入控制变量与交互项）
# ============================================================================
Xd, nm = design(df, [("lnpop", "lnpop")]);                              r2_1 = ols(y, Xd, nm)
Xd, nm = design(df, [("lnpop", "lnpop"), ("educ", "educ")]);             r2_2 = ols(y, Xd, nm)
Xd, nm = design(df, base_spec);                                          r2_3 = ols(y, Xd, nm)
Xd, nm = design(df, base_spec + [("lnpop_x_educ", "lnpop_x_educ")]);     r2_4 = ols(y, Xd, nm)
res2 = [r2_1, r2_2, r2_3, r2_4]
col2 = ["(1) 双变量\nlnpop", "(2) 多元\n+educ", "(3) 多元\n+全部控制变量", "(4) 多元\n+lnpop×educ"]
order2 = ["lnpop", "educ", "male", "marr", "exp", "exp2", "lnpop_x_educ", "_cons"]
lab2 = {"lnpop": "城市规模对数 lnpop", "educ": "受教育年限 educ", "male": "性别 male",
        "marr": "婚姻 marr", "exp": "工作经验 exp", "exp2": "工作经验平方 exp²",
        "lnpop_x_educ": "lnpop × educ", "_cons": "常数项 _cons"}
table2 = build_reg_table(res2, col2, order2, lab2)

# ============================================================================
# 表 3  虚拟变量加法模型：截距随虚拟变量变化（不含交互项）
# ============================================================================
Xd, nm = design(df, [("male", "male")]);                                  r3a = ols(y, Xd, nm)
Xd, nm = design(df, [("marr", "marr")]);                                  r3b = ols(y, Xd, nm)
Xd, nm = design(df, [("male", "male"), ("marr", "marr")]);                r3c = ols(y, Xd, nm)
Xd, nm = design(df, base_spec);                                           r3d = ols(y, Xd, nm)
Xd, nm = design(df, [("lnpop", "lnpop"), ("male", "male"), ("marr", "marr"),
                     ("educ", "educ")]);                                  r3e = ols(y, Xd, nm)
res3 = [r3a, r3b, r3c, r3d, r3e]
col3 = ["(1) 单虚拟\nmale", "(2) 单虚拟\nmarr", "(3) 双虚拟\nmale+marr",
        "(4) 加法模型\n+全部控制", "(5) 加法模型\n+educ"]
order3 = ["lnpop", "male", "marr", "educ", "exp", "exp2", "_cons"]
lab3 = {"lnpop": "城市规模对数 lnpop", "male": "性别 male（基准：女性）",
        "marr": "婚姻 marr（基准：未婚）", "educ": "受教育年限 educ",
        "exp": "工作经验 exp", "exp2": "工作经验平方 exp²", "_cons": "常数项 _cons"}
table3 = build_reg_table(res3, col3, order3, lab3)

b_exp, b_exp2 = get(r3d, "exp")[0], get(r3d, "exp2")[0]
turn_point = -b_exp / (2 * b_exp2)

# ============================================================================
# 表 4  虚拟变量乘法模型：截距 + 斜率同时变化（交互项）
# ============================================================================
t4a = []
for gv, gname, mp in [("male", "性别", {0.0: "女性（基准）", 1.0: "男性"}),
                      ("marr", "婚姻", {0.0: "未婚（基准）", 1.0: "已婚"})]:
    for k, lab in mp.items():
        s = df.loc[df[gv] == k, "lnwage"]
        t4a.append((gname, lab, int(len(s)), round(float(s.mean()), 3), round(float(s.std(ddof=1)), 3)))
    g = df.groupby(gv)["lnwage"].mean()
    lo, hi = min(mp), max(mp)
    diff = float(g[hi] - g[lo])
    t4a.append((gname, f"差值（{mp[hi]}−{mp[lo]}）", "", round(diff, 3), ""))
    t4a.append((gname, "  精确百分比（100×(e^β−1)）", "", "", f"{pct(diff):+.1f}%"))
table4a = pd.DataFrame(t4a, columns=["虚拟变量", "类别", "Obs", "lnwage 均值", "精确百分比变化"])

Xd, nm = design(df, [("male", "male"), ("marr", "marr"), ("male_x_marr", "male_x_marr")]);   r4a = ols(y, Xd, nm)
Xd, nm = design(df, [("male", "male"), ("educ", "educ"), ("male_x_educ", "male_x_educ")]);   r4b = ols(y, Xd, nm)
Xd, nm = design(df, base_spec + [("lnpop_x_educ", "lnpop_x_educ")]);                         r4c = ols(y, Xd, nm)
Xd, nm = design(df, [("c_lnpop", "c_lnpop"), ("c_educ", "c_educ"), ("clnpop_x_ceduc", "clnpop_x_ceduc"),
                     ("male", "male"), ("marr", "marr"), ("exp", "exp"), ("exp2", "exp2")])
r4d = ols(y, Xd, nm)
Xd, nm = design(df, base_spec + [("lnpop_x_male", "lnpop_x_male"), ("lnpop_x_marr", "lnpop_x_marr")])
r4e = ols(y, Xd, nm)
res4 = [r4a, r4b, r4c, r4d, r4e]
col4 = ["(1) 虚拟×虚拟\nmale×marr", "(2) 虚拟×定量\nmale×educ",
        "(3) 定量×定量\nlnpop×educ（4.37A）", "(4) 中心化\n（4.37B）", "(5) lnpop×male/marr"]
order4 = ["male", "marr", "male_x_marr", "educ", "male_x_educ", "lnpop", "c_lnpop", "c_educ",
          "lnpop_x_educ", "clnpop_x_ceduc", "lnpop_x_male", "lnpop_x_marr",
          "exp", "exp2", "_cons"]
lab4 = {"male": "性别 male", "marr": "婚姻 marr", "male_x_marr": "male × marr",
        "educ": "受教育年限 educ", "male_x_educ": "male × educ",
        "lnpop": "城市规模对数 lnpop", "c_lnpop": "lnpop − 均值", "c_educ": "educ − 均值",
        "lnpop_x_educ": "lnpop × educ", "clnpop_x_ceduc": "c_lnpop × c_educ",
        "lnpop_x_male": "lnpop × male", "lnpop_x_marr": "lnpop × marr",
        "exp": "工作经验 exp", "exp2": "工作经验平方 exp²", "_cons": "常数项 _cons"}
table4b = build_reg_table(res4, col4, order4, lab4)

b_lnpop, b_int = get(r4c, "lnpop")[0], get(r4c, "lnpop_x_educ")[0]
educ_points = [6, 9, 11.43, 12, 15, 16, 19]
marg_lnpop = pd.DataFrame([(e, round(b_lnpop + b_int * e, 4)) for e in educ_points],
                          columns=["受教育年限 educ", "lnpop 对 lnwage 的边际效应"])
Xd_f, nm_f = design(df, [("lnpop", "lnpop"), ("educ", "educ"), ("male", "male"), ("marr", "marr"), ("exp", "exp"), ("exp2", "exp2")]); r4f = ols(y, Xd_f, nm_f)
F_int = nested_f(r4f, r4c)    # 受限：无交互项；非受限：含 lnpop×educ
m_a = get(r4a, "male")[0]; r_b = get(r4a, "marr")[0]; r_i = get(r4a, "male_x_marr")[0]
cons_a = get(r4a, "_cons")[0]
groups_a = pd.DataFrame([
    ("未婚女性（基准组）", round(cons_a, 3), "—"),
    ("未婚男性", round(cons_a + m_a, 3), f"{pct(m_a):+.1f}%"),
    ("已婚女性", round(cons_a + r_b, 3), f"{pct(r_b):+.1f}%"),
    ("已婚男性", round(cons_a + m_a + r_b + r_i, 3), f"相对已婚女性 {pct(m_a + r_i):+.1f}%"),
], columns=["组别", "截距（对数工资）", "相对基准组"])

# ============================================================================
# 输出 CSV（备查）
# ============================================================================
tables = OrderedDict([("表1_描述性统计", table1), ("表2_双变量与多元回归", table2),
                      ("表3_加法模型", table3), ("表4_乘法模型", table4b)])
for k, v in tables.items():
    v.to_csv(os.path.join(OUT, f"_{k}.csv"), index=False, encoding="utf-8-sig")
for k, v in [("表1c_城市规模四分位", popq), ("表4a_分组均值", table4a),
             ("表4c_边际效应", marg_lnpop), ("表4d_四组截距", groups_a)]:
    v.to_csv(os.path.join(OUT, f"_{k}.csv"), index=False, encoding="utf-8-sig")

RESULT = dict(N=N, table1=table1, popq=popq, table2=table2, table3=table3,
              table4a=table4a, table4b=table4b, marg_lnpop=marg_lnpop, groups_a=groups_a,
              res2=res2, res3=res3, res4=res4, F_int=F_int, turn_point=turn_point)

if __name__ == "__main__":
    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 30)
    print("N =", N)
    print(table1.to_string(index=False))
    print(popq.to_string(index=False)); print(table2.to_string(index=False))
    print(table3.to_string(index=False)); print("二次项转折点 exp =", round(turn_point, 2))
    print(table4a.to_string(index=False)); print(table4b.to_string(index=False))
    print(marg_lnpop.to_string(index=False)); print(groups_a.to_string(index=False))
    print("交互项 F = %.2f, q = %d, df = %d, p = %.4g" % (F_int[0], F_int[1], F_int[2], F_int[3]))
