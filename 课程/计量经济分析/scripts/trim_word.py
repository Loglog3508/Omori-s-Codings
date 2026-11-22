# -*- coding: utf-8 -*-
"""把 make_word.py 中各表的多段解读替换为单段精简解读，并删除“结论”部分。"""
import io

P = r"C:\Users\omori\Omori-s-Codings\课程\计量经济分析\scripts\make_word.py"
src = io.open(P, encoding="utf-8-sig").read()
lines = src.split("\n")


def block(start_marker, end_marker):
    """返回 [start_idx, end_idx) 区间（0-based，含起点不含终点）"""
    i = next(k for k, l in enumerate(lines) if l.strip() == start_marker)
    j = next(k for k in range(i, len(lines)) if end_marker(lines[k]))
    return i, j


# ---------------- 表一解读 ----------------
i, j = block('h1("表一解读")',
             lambda l: l.startswith("# ==========") and "表二" in l)
new1 = '''h1("表一解读")
para(f"表一给出了回归所用 7 个变量的均值、标准差与取值范围。被解释变量 lnwage 均值 {B.df['lnwage'].mean():.3f}"
     f"（约合 {2.718281828 ** B.df['lnwage'].mean():,.0f} 元/月）、标准差 {B.df['lnwage'].std(ddof=1):.3f}，"
     "工资取对数后系数才能读成百分比变化。核心解释变量 lnpop 均值 "
     f"{mean_lnpop:.3f}、标准差 {B.df['lnpop'].std(ddof=1):.3f}，取值 {B.df['lnpop'].min():.3f}~{B.df['lnpop'].max():.3f}，"
     f"对应城市人口约 {2.718281828 ** B.df['lnpop'].min() / 1e4:.0f} 万至 {2.718281828 ** B.df['lnpop'].max() / 1e4:,.0f} 万人，"
     "跨越两个数量级，城市规模效应的识别有足够变异性；对数形式使系数成为弹性，符合 4.1 节经验法则。"
     f"educ 均值 {B.df['educ'].mean():.3f} 年、exp 均值 {B.df['exp'].mean():.3f} 年，male、marr 均值 "
     f"{B.df['male'].mean():.3f}、{B.df['marr'].mean():.3f} 即男性与已婚样本占比，各类样本量都足够充分。")
'''
lines[i:j] = new1.split("\n")

# ---------------- 表二解读 ----------------
i, j = block('h1("表二解读")',
             lambda l: l.startswith("# ==========") and "表三" in l)
new2 = '''h1("表二解读")
para(f"双对数模型下 lnpop 的系数就是弹性。列 (1) 只放城市规模，系数 {b1[0]:.3f}（标准误 {b1[1]:.3f}，{sig(b1[2])}），"
     f"即城市人口每增加 10%，工资平均高约 {b1[0]*10:.2f}%，但 R² 仅 {B.r2_1['r2']:.3f}。"
     f"列 (2) 加入个体特征后 lnpop 降为 {b2['lnpop'][0]:.3f}（{sig(b2['lnpop'][2])}），"
     "说明双变量模型存在遗漏变量偏误（大城市吸引了更多高学历者）；同时 educ 系数 "
     f"{b2['educ'][0]:.3f}（每多读一年工资高约 {P(b2['educ'][0]):.2f}%，{sig(b2['educ'][2])}），"
     f"男性比女性高约 {P(b2['male'][0]):.1f}%（{sig(b2['male'][2])}），已婚者比未婚者高约 {P(b2['marr'][0]):.1f}%"
     f"（{sig(b2['marr'][2])}）；exp 一次项显著为正、二次项显著为负，工资随经验先升后降，顶点约 "
     f"{-b2['exp'][0] / (2 * b2['exp2'][0]):.1f} 年；以“健康”为基准，D(基本健康) {b2['h2'][0]:.3f}、"
     f"D(不健康) {b2['h3'][0]:.3f} 均显著为负，R² 升至 {B.r2_2['r2']:.3f}。"
     f"列 (3) 控制行业与职业固定效应后 lnpop 仍为 {b3['lnpop'][0]:.3f}（{sig(b3['lnpop'][2])}），"
     "说明城市溢价不是通过行业职业结构实现的；而 educ、male 系数明显下降，说明部分人力资本与性别差异"
     f"是经由行业职业选择传导的，R² 达 {B.r2_3['r2']:.3f}。列 (4) 加入 lnpop×educ，交互项 "
     f"{b4['lnpop_x_educ'][0]:.3f}（{sig(b4['lnpop_x_educ'][2])}）显著，此时 lnpop（{b4['lnpop'][0]:.3f}）、"
     f"educ（{b4['educ'][0]:.3f}）主效应已变成“educ=0”“人口为 1 人”时的外推值，无经济含义，须按边际效应解读（见表四）。")
'''
lines[i:j] = new2.split("\n")

# ---------------- 表三解读 ----------------
i, j = block('h1("表三解读")',
             lambda l: l.startswith("# ==========") and "表四" in l)
new3 = '''h1("表三解读")
para(f"加法模型只改变截距、不改变斜率：常数项 {b3['_cons'][0]:.3f} 是基准组（女性、未婚、健康）的截距，"
     f"其他组在其上平移。male 系数 {b3['male'][0]:.3f}（标准误 {b3['male'][1]:.3f}，{sig(b3['male'][2])}），"
     f"控制其他因素后男性工资比女性高约 {P(b3['male'][0]):.1f}%（精确换算 100×(e^β−1)%）；marr 系数 "
     f"{b3['marr'][0]:.3f}（{sig(b3['marr'][2])}），已婚者高约 {P(b3['marr'][0]):.1f}%。"
     f"健康状况按“m 类取 m−1 个”只引入两个虚拟变量：D(基本健康) {h2[0]:.4f}（标准误 {h2[1]:.4f}，{sig(h2[2])}，"
     f"低约 {abs(P(h2[0])):.1f}%）、D(不健康) {h3[0]:.4f}（标准误 {h3[1]:.4f}，{sig(h3[2])}，低约 {abs(P(h3[0])):.1f}%），"
     "两者均显著为负且绝对值递增，健康对工资的影响单调；若三类虚拟变量全放会与常数项完全共线，陷入虚拟变量陷阱。"
     f"lnpop、educ、exp 系数与表二列 (3) 相同（{b3['lnpop'][0]:.3f}、{b3['educ'][0]:.3f}、{b3['exp'][0]:.3f}，均显著），"
     f"R² {B.r2_3['r2']:.3f}。其局限是假定各群体斜率相同，一旦斜率存在差异就需引入交互项，即表四。")
'''
lines[i:j] = new3.split("\n")

# ---------------- 表四解读 ----------------
i, j = block('h1("表四解读")',
             lambda l: l.startswith("# ==========") and "结论" in l)
new4 = '''h1("表四解读")
para(f"列 (1) 令 male 与 marr 相乘，四组人各有截距：未婚女性 {i1['_cons'][0]:.3f}（基准）、未婚男性 "
     f"{i1['_cons'][0] + i1['male'][0]:.3f}、已婚女性 {i1['_cons'][0] + i1['marr'][0]:.3f}、已婚男性 "
     f"{i1['_cons'][0] + i1['male'][0] + i1['marr'][0] + i1['male_x_marr'][0]:.3f}；交互项 {i1['male_x_marr'][0]:.3f}"
     f"（标准误 {i1['male_x_marr'][1]:.3f}，{sig(i1['male_x_marr'][2])}）说明男性的工资优势在已婚群体中再高约 "
     f"{P(i1['male'][0] + i1['male_x_marr'][0]):.1f}%，而 marr 主效应 {i1['marr'][0]:.3f} 不显著，"
     "即婚姻溢价几乎只存在于男性身上——这是加法模型捕捉不到的异质性。"
     f"列 (2) 令 male×educ：女性教育回报 {i2['educ'][0]:.3f}（{sig(i2['educ'][2])}），男性为 "
     f"{i2['educ'][0] + i2['male_x_educ'][0]:.3f}，交互项 {i2['male_x_educ'][0]:.3f}"
     f"（标准误 {i2['male_x_educ'][1]:.3f}，{sig(i2['male_x_educ'][2])}），教育回报无性别差异，性别差距主要表现为截距平移。"
     f"列 (3) 为教材例 4.37A：lnpop {i3['lnpop'][0]:.3f}、educ {i3['educ'][0]:.3f} 看似反常，实为 educ=0、"
     f"人口为 1 人时的外推值；有意义的边际效应 ∂lnwage/∂lnpop = {i3['lnpop'][0]:.3f} + "
     f"{i3['lnpop_x_educ'][0]:.3f}·educ，在均值教育 {mean_educ:.2f} 年处为 "
     f"{i3['lnpop'][0] + i3['lnpop_x_educ'][0] * mean_educ:.3f}，16 年教育处升至 "
     f"{i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 16:.3f}，6 年教育处仅 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 6:.3f}，"
     f"即学历越高越能分享大城市溢价；联合检验 F(1, {F_int[2]}) = {F_int[0]:.2f}，p < 0.001。"
     f"列 (4) 按 4.37B 先中心化再相乘，交互项与 R² 不变，但主效应恢复可解释：中心化 lnpop {i4['c_lnpop'][0]:.3f}"
     f"（{sig(i4['c_lnpop'][2])}）为均值学历者的城市规模弹性，中心化 educ {i4['c_educ'][0]:.3f}（{sig(i4['c_educ'][2])}）"
     f"为均值规模城市的教育回报。列 (5) 令 lnpop 与性别婚姻交互：lnpop×male {i5['lnpop_x_male'][0]:.3f}"
     f"（{sig(i5['lnpop_x_male'][2])}）、lnpop×marr {i5['lnpop_x_marr'][0]:.3f}（{sig(i5['lnpop_x_marr'][2])}），"
     "女性从城市规模扩大中获益略多，婚姻与城市规模交互较弱；综合看最稳健的交互效应是 lnpop×educ。")
'''
lines[i:j] = new4.split("\n")

io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("done, lines:", len(lines))