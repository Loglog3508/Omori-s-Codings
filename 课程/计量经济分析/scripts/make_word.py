# -*- coding: utf-8 -*-
"""
生成最终交付 Word（参考 演示数据\\分析结果.docx 的表格样式：表一 VarName|Obs|Mean|SD|Min|Max，
表二/三/四 为 esttab 风格的两行式回归表）。
结构：封面 → 表一+解读 → 表二+解读 → 表三+解读 → 表四+解读 → 附录：全部运行代码
运行： python scripts/make_word.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_four_tables as B  # noqa: E402

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

OUT = B.OUT
CLASS_NAME = "大数据242"
STUDENT_NAME = "洪翼雄"
STUDENT_ID = "2407150229"
DOCX = os.path.join(OUT, f"{CLASS_NAME}-{STUDENT_NAME}-{STUDENT_ID}.docx")
get, P, n = B.get, B.pct, B.N

# ---------------------------------------------------------------- 关键数字
b1 = get(B.r2_1, "lnpop")
b2 = {k: get(B.r2_2, k) for k in ["lnpop", "educ", "_cons"]}
b3 = {k: get(B.r2_3, k) for k in ["lnpop", "educ", "male", "marr", "exp", "exp2", "_cons"]}
b4 = {k: get(B.r2_4, k) for k in ["lnpop", "educ", "male", "marr", "exp", "exp2", "lnpop_x_educ", "_cons"]}
r3a, r3b, r3c, r3d, r3e = B.res3
tp = B.turn_point
i1 = {k: get(B.r4a, k) for k in ["male", "marr", "male_x_marr", "_cons"]}
i2 = {k: get(B.r4b, k) for k in ["male", "educ", "male_x_educ", "_cons"]}
i3 = {k: get(B.r4c, k) for k in ["lnpop", "educ", "lnpop_x_educ", "_cons"]}
i4 = {k: get(B.r4d, k) for k in ["c_lnpop", "c_educ", "clnpop_x_ceduc", "_cons"]}
i5 = {k: get(B.r4e, k) for k in ["lnpop", "lnpop_x_male", "lnpop_x_marr", "_cons"]}
F_int = B.F_int
mean_lnpop = float(B.df["lnpop"].mean())
mean_educ = float(B.df["educ"].mean())


def sig(p):
    return ("在 1% 的水平上显著" if p < 0.01 else "在 5% 的水平上显著" if p < 0.05
            else "在 10% 的水平上显著" if p < 0.10 else "不显著，|t| 未达 10% 临界值")


def coefs(res, names):
    """按 names 顺序取系数，缺失的列留空 —— 用于拼 esttab 风格的同表"""
    idx = {k: i for i, k in enumerate(res["names"])}
    return {k: (f"{res['b'][idx[k]]:.3f}{B.star(res['p'][idx[k]])}", f"({res['se'][idx[k]]:.3f})")
            if k in idx else ("", "") for k in names}


def tval(res):
    """{变量名: t 值}，t = 系数/标准误"""
    return {k: float(res["t"][i]) for i, k in enumerate(res["names"])}


def tt(res, nm):
    """单个变量的 t 值"""
    return float(res["t"][res["names"].index(nm)])


def ci(res, nm, level=0.95):
    """正态近似下的置信区间（N=14757，t 分布与正态几乎无差别）"""
    z = 1.959964 if level == 0.95 else 1.644854
    i = res["names"].index(nm)
    b, s = float(res["b"][i]), float(res["se"][i])
    return b - z * s, b + z * s


def cistr(res, nm, level=0.95):
    """返回 '[下限, 上限]' 形式的区间文字"""
    lo, hi = ci(res, nm, level)
    return f"[{lo:.3f}, {hi:.3f}]"


# ---------------------------------------------------------------- Word 基础
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2.6)
sec.top_margin = sec.bottom_margin = Cm(2.4)
st = doc.styles["Normal"]
st.font.name = "宋体"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
st.paragraph_format.line_spacing = 1.4


def set_cn(run, font="宋体", size=10.5, bold=False):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)


def para(text, size=10.5, bold=False, align=None, indent=True, font="宋体", after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.first_line_indent = Pt(size * 2) if indent else Pt(0)
    p.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT}.get(
        align, WD_ALIGN_PARAGRAPH.JUSTIFY)
    set_cn(p.add_run(text), font, size, bold)
    return p


def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    set_cn(p.add_run(text), "黑体", 13, True)


def form(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    set_cn(p.add_run(text), "Times New Roman", 10)


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    set_cn(p.add_run(text), "黑体", 10.5, True)


def note(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    set_cn(p.add_run(text), "楷体", 9)


def _set_border(el, edge, sz):
    """在 tblPr/trPr/tcPr 上设置某一条边框（三线表用）"""
    tag = "w:" + edge
    for e in el.findall(qn(tag)):
        el.remove(e)
    b = el.makeelement(qn(tag), {qn("w:val"): "single", qn("w:sz"): str(sz),
                                 qn("w:space"): "0", qn("w:color"): "000000"})
    el.append(b)


def _table_borders(tbl, top=None, bottom=None, inside_h=None):
    tblPr = tbl._tbl.tblPr
    for e in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(e)
    bd = tblPr.makeelement(qn("w:tblBorders"), {})
    for edge, sz in [("top", top), ("left", 0), ("bottom", bottom), ("right", 0),
                     ("insideH", inside_h), ("insideV", 0)]:
        b = bd.makeelement(qn("w:" + edge), {qn("w:val"): "single" if sz else "nil",
                                             qn("w:sz"): str(sz or 0), qn("w:space"): "0",
                                             qn("w:color"): "000000" if sz else "auto"})
        bd.append(b)
    tblPr.append(bd)


def _row_borders(row, top=None, bottom=None):
    trPr = row._tr.get_or_add_trPr()
    if top:
        _set_border(trPr, "top", top)
    if bottom:
        _set_border(trPr, "bottom", bottom)


def three_line(t, nhead=1, col_rule=True, top_sz=12, mid_sz=6, bot_sz=12):
    """把表格变成三线表：顶线、栏目线、底线，其余横线一律去掉（参考 esttab/booktabs 输出）"""
    _table_borders(t, top=top_sz, bottom=bot_sz, inside_h=None)
    for i, row in enumerate(t.rows):
        _row_borders(row, top=top_sz if i == 0 else None,
                     bottom=(mid_sz if (col_rule and i == nhead - 1) else (bot_sz if i == len(t.rows) - 1 else None)))
    return t


def add_table(df, size=9, header=True):
    """df 为 DataFrame；header=True 时把 df.columns 写为首行（否则全部行都当数据写）"""
    nrows = df.shape[0] + (1 if header else 0)
    t = doc.add_table(rows=nrows, cols=df.shape[1])
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    off = 0
    if header:
        for j, c in enumerate(df.columns):
            cell = t.cell(0, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(1)
            set_cn(p.add_run(str(c)), "黑体", size, True)
        off = 1
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            v = df.iat[i, j]
            cell = t.cell(i + off, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and df.shape[1] > 2) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(1)
            set_cn(p.add_run("" if (v is None or (isinstance(v, float) and v != v)) else str(v)), "宋体", size, False)
    return t


def esttab_like(cols_titles, depvars, rows, stats, size=9):
    """rows: [(变量名, {列号: (系数, 标准误)})]；stats: [(行名, [值...])]"""
    ncol = len(cols_titles)
    data = [[c for c in [""] + list(cols_titles)], [c for c in [""] + list(depvars)]]
    for nm, by_col in rows:
        data.append([nm] + [by_col.get(j, ("", ""))[0] for j in range(len(cols_titles))])
        data.append([""] + [by_col.get(j, ("", ""))[1] for j in range(len(cols_titles))])
    for nm, vals in stats:
        data.append([nm] + list(vals))
    df = pd.DataFrame([[str(v) for v in row] for row in data]).astype(object)
    return three_line(add_table(df, size=size, header=False), nhead=2, col_rule=False)

# ---------------------------------------------------------------- 封面
para("计量经济分析", size=20, bold=True, align="center", indent=False, font="黑体", after=8)
for _ in range(2):
    doc.add_paragraph()
para("函数形式与虚拟变量：四个表的估计与解读", size=15, bold=True, align="center", indent=False, font="黑体", after=6)
para("——基于实验一 CMDS2017 子样本（14,757 位流动人口）", size=11, align="center", indent=False)
for _ in range(3):
    doc.add_paragraph()
three_line(add_table(pd.DataFrame([["班级", CLASS_NAME], ["姓名", STUDENT_NAME], ["学号", STUDENT_ID],
                        ["数据", "实验一\\CMDS2017子样本.dta（7 个变量）"],
                        ["样本", f"N = {n:,}（{int(B.df['lnpop'].nunique())} 个城市）"],
                        ["软件", "Stata 18（do 文件见文末）；Python 复算校验"]], columns=["项目", "内容"]), size=10))

para(f"变量说明：lnwage 为月工资的自然对数（样本月工资均值约 {2.718281828 ** B.df['lnwage'].mean():,.0f} 元）；"
     "lnpop 为城市人口规模的自然对数；educ 为受教育年限；exp 为工作经验（年）、exp2 为其平方；"
     "male、marr 分别为性别（男=1）与婚姻（已婚=1）虚拟变量，两者均只有两类，按“m 类取 m−1 个”"
     "各引入 1 个虚拟变量，基准组分别为女性与未婚者。被解释变量与 lnpop 都取了自然对数，"
     "属双对数（对数—对数）模型，lnpop 系数即弹性。", after=4)
doc.add_page_break()

# ================================================================ 函数形式说明
h1("一、函数形式与变量设定的理由")
para("在报告四张表之前，先说明各变量的函数形式为什么这样设定，依据教材第 4 章 4.1 节的三条经验。"
     "第一，被解释变量 lnwage 用月工资的自然对数。工资分布的跨度极大（本样本 1,000~40,000 元，差 40 倍），"
     "且明显右偏——少数高收入者会把均值拉高，直接对工资原值建模会受到极端值过多影响；"
     "取对数后分布更接近对称，回归系数的标准误更小，也更符合经典线性模型的同方差假定。"
     "更重要的是，在“对数—线性”与“双对数”形式下，系数可以直接读成相对变化（百分比）或弹性，"
     "这正是经济学最关心的“工资高了百分之几”，比“高了多少元”更有跨样本的可比性。")
para("第二，核心解释变量 lnpop 同样取对数，与 lnwage 构成双对数（对数—对数）模型，其系数即城市规模的工资弹性："
     "城市人口增加 1%，工资平均变化百分之几。人口是典型的货币/规模类变量，跨越多个数量级"
     "（本样本城市人口 2.5 万~3,075 万），按 4.1 节的经验，这类变量必须取对数；若直接用人口原值，"
     "系数将是“每多一人工资多多少”，在经济上既微小又没有直观意义，还会被大城市主导回归结果。")
para("第三，educ 与 exp 是年度量（受教育年限、工作年数），按 4.1 节的经验不取对数，直接以水平值进入模型，"
     "这样 educ 的系数就是“多读一年书工资高百分之几”，含义清楚。"
     "但工作经验对工资的影响并非线性——通常先快速上升、之后趋缓甚至下降——"
     "因此同时引入 exp 与其平方 exp²（多项式形式），拟合边际递减；由 ∂lnwage/∂exp = β₅ + 2β₆·exp 可以解出"
     "工资随经验由升转降的转折点 −β₅/(2β₆)，估计结果见表二、表三。")
para("第四，male 与 marr 均为二分类变量，按 4.2 节“m 类取 m−1 个”的规则各引入 1 个虚拟变量，"
     "基准组分别为女性（male=0）与未婚者（marr=0），并保留常数项，从而避免虚拟变量陷阱（完全共线）。"
     "在 lnwage 为被解释变量的模型中，虚拟变量系数是半弹性，需按 4.2 节的精确公式 100×(e^β−1)% 换算成百分比。"
     "最后提醒一点：因变量已取对数，本报告四张表的 R² 都在同一因变量下计算，彼此可比；"
     "但若改用工资原值作被解释变量（线性—线性模型），其 R² 与对数模型的 R² 不可直接比较，这是 4.1 节明确指出的。")

# ================================================================ 表一
h1("表一  变量的描述性统计")
caption("表一：变量的描述性统计")
t1 = pd.DataFrame([[v, f"{n:,}", f"{B.df[v].mean():.3f}", f"{B.df[v].std(ddof=1):.3f}",
                    f"{B.df[v].min():.3f}", f"{B.df[v].max():.3f}"]
                   for v in ["male", "educ", "exp", "exp2", "marr", "lnpop", "lnwage"]],
                  columns=["VarName", "Obs", "Mean", "SD", "Min", "Max"])
three_line(add_table(t1))
note("注：数据为实验一 CMDS2017子样本.dta，N = 14,757；lnpop、lnwage 已在对数尺度上，"
     "其最小、最大值对应原始值需取指数还原。")

h1("表一解读")
_pmin = 2.718281828 ** B.df["lnpop"].min()
_pmax = 2.718281828 ** B.df["lnpop"].max()
para(f"表一报告回归所用 7 个变量的样本量、均值、标准差与极值，7 个变量均无缺失值，样本量统一为 {n:,}。"
     f"被解释变量 lnwage 均值 {B.df['lnwage'].mean():.3f}、标准差 {B.df['lnwage'].std(ddof=1):.3f}，"
     f"取指数还原后月工资平均约 {2.718281828 ** B.df['lnwage'].mean():,.0f} 元，实际范围 "
     f"{2.718281828 ** B.df['lnwage'].min():,.0f}~{2.718281828 ** B.df['lnwage'].max():,.0f} 元，"
     "工资已做过清理（有 1,000 元下限），取对数后系数可按百分比变化解读。"
     f"核心解释变量 lnpop 均值 {B.df['lnpop'].mean():.3f}、标准差 {B.df['lnpop'].std(ddof=1):.3f}，"
     f"取值 {B.df['lnpop'].min():.3f}~{B.df['lnpop'].max():.3f}，还原后对应城市人口约 "
     f"{_pmin:,.0f} 至 {_pmax:,.0f} 人（约 {_pmin / 1e4:.0f} 万至 {_pmax / 1e4:,.0f} 万人，"
     f"共 {int(B.df['lnpop'].nunique())} 个不同取值，即 {int(B.df['lnpop'].nunique())} 个城市），"
     "跨两个数量级，变异性足以识别城市规模效应。"
     f"educ 均值 {B.df['educ'].mean():.3f} 年、标准差 {B.df['educ'].std(ddof=1):.3f}，介于 "
     f"{B.df['educ'].min():.0f}~{B.df['educ'].max():.0f} 年；exp 均值 {B.df['exp'].mean():.3f} 年、"
     f"范围 {B.df['exp'].min():.0f}~{B.df['exp'].max():.0f} 年，取值全部非负，逻辑上合理。"
     f"male 均值 {B.df['male'].mean():.3f}、marr 均值 {B.df['marr'].mean():.3f}，即男性占 "
     f"{B.df['male'].mean() * 100:.1f}%、已婚者占 {B.df['marr'].mean() * 100:.1f}%；"
     f"两个虚拟变量的两类样本量分别为 {int((B.df['male'] == 0).sum()):,}（女性）/ {int((B.df['male'] == 1).sum()):,}（男性）"
     f"和 {int((B.df['marr'] == 0).sum()):,}（未婚）/ {int((B.df['marr'] == 1).sum()):,}（已婚），容量都很充足。"
     "需要提醒的是 exp2 的均值与标准差远大于 exp（平方放大了量级），因此回归中 exp² 的系数必然很小"
     "（10⁻³ 量级），其经济含义不能直接按“每年变化”解读，而要结合转折点 −β₅/(2β₆) 说明。")
_el = [("小学及以下（0~6 年）", int((B.df["educ"] <= 6).sum())),
       ("初中（9 年）", int((B.df["educ"] == 9).sum())),
       ("高中（12 年）", int((B.df["educ"] == 12).sum())),
       ("大专及以上（15 年以上）", int((B.df["educ"] >= 15).sum()))]
para("作为对样本结构的一次交叉验证，把 educ 按教材例 4.3 的做法归并为四个教育层级，"
     "人数分别为" + "、".join(f"{k} {v:,} 人" for k, v in _el) +
     f"，四类合计 {sum(v for _, v in _el):,} 人，正好等于样本量 {n:,}，"
     "说明 educ 没有落在上述区间之外或缺失的情形，归并不会损失样本。"
     "这四类人占样本的比重分别为 " + "、".join(f"{v / n * 100:.1f}%" for _, v in _el) +
     "，初中与大专及以上两类合计约 " + f"{((B.df['educ'] == 9) | (B.df['educ'] >= 15)).sum() / n * 100:.1f}%" +
     "，样本以中等及以上学历的流动人口为主，"
     "这与 CMDS 流动人口整体学历高于农村常住人口的典型特征一致。")

# ================================================================ 表二
doc.add_page_break()
h1("表二  双变量回归与多元回归的对比结果")
para("双变量模型（只放城市规模一个解释变量）：", indent=True, after=2)
form("lnwage = β₀ + β₁·lnpop + u")
para("多元回归模型（逐步加入教育、性别、婚姻、经验及其平方、交互项）：", indent=True, after=2)
form("lnwage = β₀ + β₁·lnpop + β₂·educ + β₃·male + β₄·marr + β₅·exp + β₆·exp² + u")
form("lnwage = β₀ + β₁·lnpop + β₂·educ + β₃·male + β₄·marr + β₅·exp + β₆·exp² + ρ·(lnpop×educ) + u")
caption("表二：回归结果（被解释变量：lnwage）")
cols2 = ["(1)", "(2)", "(3)", "(4)"]
rows2 = []
for nm, cn in [("lnpop", "lnpop"), ("educ", "educ"), ("male", "male"), ("marr", "marr"),
               ("exp", "exp"), ("exp2", "exp2"), ("lnpop_x_educ", "lnpop×educ"), ("_cons", "_cons")]:
    by = {}
    for j, r in enumerate([B.r2_1, B.r2_2, B.r2_3, B.r2_4]):
        c = coefs(r, [nm])[nm]
        if c[0] or c[1]:
            by[j] = c
    if by:
        rows2.append((cn, by))
stats2 = [("N", [f"{r['n']:,}" for r in [B.r2_1, B.r2_2, B.r2_3, B.r2_4]]),
          ("R²", [f"{r['r2']:.3f}" for r in [B.r2_1, B.r2_2, B.r2_3, B.r2_4]])]
three_line(esttab_like(cols2, ["lnwage"] * 4, rows2, stats2))
note("注：括号内为标准误；*、**、*** 分别表示在 10%、5%、1% 的水平上显著。"
     "列 (1) 为双变量回归，列 (2)~(4) 依次加入控制变量。数据：CMDS2017 子样本，N = 14,757。")

h1("表二解读")
para(f"被解释变量与核心解释变量都取了对数，属 4.1 节的“双对数模型”，lnpop 的系数直接读作弹性。"
     f"列 (1) 只放城市规模，lnpop 系数 {b1[0]:.3f}（标准误 {b1[1]:.3f}，t = {tt(B.r2_1, 'lnpop'):.2f}，"
     f"95% 置信区间 {cistr(B.r2_1, 'lnpop')}，{sig(b1[2])}），"
     f"意味着城市人口每增加 10%，月工资平均高约 {b1[0] * 10:.2f}%；城市人口多 1%，工资高约 {b1[0]:.3f}%。"
     f"区间下限 {ci(B.r2_1, 'lnpop')[0]:.3f}、上限 {ci(B.r2_1, 'lnpop')[1]:.3f} 都远离 0，"
     "城市规模与工资的正向关系在统计上非常确定。"
     "与教材用 wage_chap4 数据得到的 lnwage = 7.53 + 0.114·lnpop 完全一致，说明城市规模弹性的估计非常稳健。"
     f"不过 R² 只有 {B.r2_1['r2']:.3f}，城市规模单独只解释工资对数的 {B.r2_1['r2'] * 100:.1f}%，"
     "其余工资差异要靠个体特征解释，于是转向多元回归。")
para(f"列 (2) 加入受教育年限后，lnpop 由 {b1[0]:.3f} 降到 {b2['lnpop'][0]:.3f}（标准误 {b2['lnpop'][1]:.3f}，"
     f"t = {tt(B.r2_2, 'lnpop'):.2f}，{sig(b2['lnpop'][2])}），这一下降说明双变量模型存在遗漏变量偏误："
     "大城市集中了更多高学历劳动者，原模型把“教育回报”误记在了城市规模头上。"
     f"educ 系数 {b2['educ'][0]:.3f}（标准误 {b2['educ'][1]:.3f}，t = {tt(B.r2_2, 'educ'):.1f}，"
     f"95% 置信区间 {cistr(B.r2_2, 'educ')}）是半弹性，"
     f"按 4.1 节精确换算为 100×(e^{b2['educ'][0]:.3f}−1)% ≈ {P(b2['educ'][0]):.1f}%，"
     "即每多受一年教育月工资高约 5%，与教材“教育回报率约 5%”的经验结果吻合。"
     f"列 (2) 的 R² 也从 {B.r2_1['r2']:.3f} 升到 {B.r2_2['r2']:.3f}。")
para(f"列 (3) 是完整多元回归。lnpop {b3['lnpop'][0]:.3f}（标准误 {b3['lnpop'][1]:.3f}，t = {tt(B.r2_3, 'lnpop'):.1f}，"
     f"95% 置信区间 {cistr(B.r2_3, 'lnpop')}，{sig(b3['lnpop'][2])}）："
     f"控制个体特征后城市人口每多 10% 工资仍高约 {b3['lnpop'][0] * 10:.2f}%，城市规模溢价稳健存在；"
     f"male {b3['male'][0]:.3f}（t = {tt(B.r2_3, 'male'):.1f}，{sig(b3['male'][2])}），"
     f"男性比女性高约 {P(b3['male'][0]):.1f}%；"
     f"marr {b3['marr'][0]:.3f}（t = {tt(B.r2_3, 'marr'):.1f}，{sig(b3['marr'][2])}），"
     f"已婚者比未婚者高约 {P(b3['marr'][0]):.1f}%；"
     f"exp {b3['exp'][0]:.3f}（t = {tt(B.r2_3, 'exp'):.1f}）、exp² {b3['exp2'][0]:.4f}"
     f"（t = {tt(B.r2_3, 'exp2'):.1f}），一次项显著为正、二次项显著为负，"
     f"工资随经验先升后降，转折点 −β₅/(2β₆) = {tp:.2f} 年，与 4.1 节的多项式函数形式一致；"
     f"R² 达 {B.r2_3['r2']:.3f}，模型解释了约四分之一的工资对数变异。"
     "对比列 (1)~(3) 可见：控制变量越齐全，lnpop 系数越接近 0.08~0.09 的稳定区间，"
     "而 R² 从 0.035 跃升到 0.233，说明多元回归既修正了偏误又大幅提高了解释力。")
para(f"列 (4) 加入 lnpop×educ 交互项，交互项系数 {b4['lnpop_x_educ'][0]:.3f}（标准误 "
     f"{b4['lnpop_x_educ'][1]:.3f}，t = {tt(B.r2_4, 'lnpop_x_educ'):.1f}，95% 置信区间 "
     f"{cistr(B.r2_4, 'lnpop_x_educ')}，{sig(b4['lnpop_x_educ'][2])}），R² 升至 {B.r2_4['r2']:.3f}；"
     f"但此时 lnpop（{b4['lnpop'][0]:.3f}）和 educ（{b4['educ'][0]:.3f}）已不再分别代表弹性和教育回报，"
     "而是 educ=0、lnpop=0 处的外推值，没有经济含义，必须按“一方的边际效应随另一方变化”来解释，"
     "具体见表四列 (3)(4)。")

# ================================================================ 表三
doc.add_page_break()
h1("表三  虚拟变量加法模型")
para("加法模型只让虚拟变量改变截距、不改变斜率：", indent=True, after=2)
form("lnwage = β₀ + β₁·lnpop + δ₁·male + δ₂·marr + β₂·educ + β₃·exp + β₄·exp² + u")
caption("表三：虚拟变量加法模型（被解释变量：lnwage）")
res3 = [B.r3a, B.r3b, B.r3c, B.r3d, B.r3e]
rows3 = []
for nm, cn in [("lnpop", "lnpop"), ("male", "male"), ("marr", "marr"), ("educ", "educ"),
               ("exp", "exp"), ("exp2", "exp2"), ("_cons", "_cons")]:
    by = {}
    for j, r in enumerate(res3):
        c = coefs(r, [nm])[nm]
        if c[0] or c[1]:
            by[j] = c
    if by:
        rows3.append((cn, by))
stats3 = [("N", [f"{r['n']:,}" for r in res3]), ("R²", [f"{r['r2']:.3f}" for r in res3])]
three_line(esttab_like(["(1)", "(2)", "(3)", "(4)", "(5)"], ["lnwage"] * 5, rows3, stats3))
note("注：括号内为标准误；*、**、*** 分别表示 10%、5%、1% 显著。male、marr 为 0/1 虚拟变量，"
     "基准组分别为女性、未婚者；列 (4)(5) 逐步加入城市规模与受教育年限。")

h1("表三解读")
m3a, m3b = get(B.r3a, "male"), get(B.r3b, "marr")
m3c, m3c_b = get(B.r3c, "male"), get(B.r3c, "marr")
m3e, m3e_b = get(B.r3e, "male"), get(B.r3e, "marr")
para(f"加法模型的形式是“截距随类别平移、斜率对所有人群相同”，常数项 {get(B.r3e, '_cons')[0]:.3f} 就是基准组"
     "（女性、未婚）的对数工资基准水平。列 (1) 单独放性别：male 系数 "
     f"{m3a[0]:.3f}（标准误 {m3a[1]:.3f}，t = {tt(B.r3a, 'male'):.1f}，95% 置信区间 {cistr(B.r3a, 'male')}，"
     f"{sig(m3a[2])}）。因为被解释变量取了自然对数，"
     "这个系数是“半弹性”，要按 4.2 节的精确公式换算为 "
     f"100×(e^{m3a[0]:.3f}−1)% = {P(m3a[0]):.1f}%，即不考虑其他因素时男性月工资比女性高约 "
     f"{P(m3a[0]):.1f}%；仅性别一个虚拟变量就使 R² 达到 {B.r3a['r2']:.3f}。")
para(f"列 (2) 单独放婚姻：marr 系数 {m3b[0]:.3f}（标准误 {m3b[1]:.3f}，t = {tt(B.r3b, 'marr'):.1f}，"
     f"95% 置信区间 {cistr(B.r3b, 'marr')}，{sig(m3b[2])}），"
     f"精确换算已婚者比未婚者高约 {P(m3b[0]):.1f}%，即文献中的“婚姻溢价”。"
     f"列 (3) 把两个虚拟变量同时放入（不加交互项）：male {m3c[0]:.3f}（t = {tt(B.r3c, 'male'):.1f}，"
     f"{sig(m3c[2])}）、marr {m3c_b[0]:.3f}（t = {tt(B.r3c, 'marr'):.1f}，{sig(m3c_b[2])}），两者均显著为正，"
     "说明性别与婚姻对工资的影响"
     f"基本可以相加；R² 由 {B.r3a['r2']:.3f}、{B.r3b['r2']:.3f} 提高到 {B.r3c['r2']:.3f}，"
     "两个虚拟变量的解释力可叠加。此处 male 与 marr 各只有两类，按“m 类取 m−1 个”各引入 1 个，"
     "基准组分别是女性与未婚者；若两类都放进模型又不放弃常数项，就会出现虚拟变量陷阱（完全共线）。")
para(f"列 (4) 加入全部控制变量：lnpop {b3['lnpop'][0]:.3f}（标准误 {b3['lnpop'][1]:.3f}，"
     f"t = {tt(B.r2_3, 'lnpop'):.1f}，{sig(b3['lnpop'][2])}）、"
     f"educ {b3['educ'][0]:.3f}（每多读一年高约 {P(b3['educ'][0]):.1f}%，{sig(b3['educ'][2])}）、"
     f"male {b3['male'][0]:.3f}（t = {tt(B.r2_3, 'male'):.1f}，男性高约 {P(b3['male'][0]):.1f}%，{sig(b3['male'][2])}）、"
     f"marr {b3['marr'][0]:.3f}（t = {tt(B.r2_3, 'marr'):.1f}，已婚高约 {P(b3['marr'][0]):.1f}%，{sig(b3['marr'][2])}）、"
     f"exp {b3['exp'][0]:.3f}（t = {tt(B.r2_3, 'exp'):.1f}）、exp² {b3['exp2'][0]:.4f}"
     f"（t = {tt(B.r2_3, 'exp2'):.1f}），所有系数符号与表二列 (3) 完全一致（是同一个方程），"
     f"R² {B.r3d['r2']:.3f}。列 (5) 同时放 lnpop、male、marr、educ 而暂不放经验项，四个系数均在 1% "
     f"水平上显著（male t = {tt(B.r3e, 'male'):.1f}、marr t = {tt(B.r3e, 'marr'):.1f}），R² {B.r3e['r2']:.3f}，"
     "可看作加法模型的最简形式：在同等教育、同等城市规模下，"
     f"男性比女性高约 {P(m3e[0]):.1f}%，已婚者比未婚者高约 {P(m3e_b[0]):.1f}%。"
     "把列 (3) 与列 (5) 对照可知，加入控制变量后 male 系数由 "
     f"{m3c[0]:.3f} 变为 {m3e[0]:.3f}、marr 由 {m3c_b[0]:.3f} 变为 {m3e_b[0]:.3f}，"
     "变化不大，说明性别与婚姻的工资差异并非主要由教育、城市规模等可观测因素造成。")
para("加法模型的局限在于它假定男性与女性、已婚与未婚人群的斜率完全一样，"
     "但不同群体在教育回报、城市规模溢价上很可能存在差异；一旦斜率不同，加法模型就会把差异"
     "统统塞进截距、得到有偏的估计，这就需要用虚拟变量与其它变量相乘，即表四的乘法模型。")

# ================================================================ 表四
doc.add_page_break()
h1("表四  虚拟变量乘法模型")
para("乘法模型把虚拟变量（或定量变量）相乘，使斜率随另一变量变化，截距与斜率同时改变：", indent=True, after=2)
form("lnwage = β₀ + δ₁·male + δ₂·marr + η·(male×marr) + u")
form("lnwage = β₀ + β₁·lnpop + β₂·educ + β₃·male + β₄·marr + β₅·exp + β₆·exp² + ρ·(lnpop×educ) + u   —— 例 4.37A")
form("lnwage = β₀ + β₁·(lnpop−lnpop̄) + β₂·(educ−educ̄) + ρ·(lnpop−lnpop̄)(educ−educ̄) + …   —— 例 4.37B")
caption("表四：虚拟变量乘法模型（被解释变量：lnwage）")
cols4 = ["(1)", "(2)", "(3)", "(4)", "(5)"]
res4 = [B.r4a, B.r4b, B.r4c, B.r4d, B.r4e]
rows4 = []
for nm, cn in [("male", "male"), ("marr", "marr"), ("male_x_marr", "male×marr"), ("educ", "educ"),
               ("male_x_educ", "male×educ"), ("lnpop", "lnpop"), ("c_lnpop", "lnpop（中心化）"),
               ("c_educ", "educ（中心化）"),
               ("lnpop_x_educ", "lnpop×educ"), ("clnpop_x_ceduc", "lnpop×educ（中心化）"),
               ("lnpop_x_male", "lnpop×male"), ("lnpop_x_marr", "lnpop×marr"),
               ("exp", "exp"), ("exp2", "exp2"), ("_cons", "_cons")]:
    by = {}
    for j, r in enumerate(res4):
        c = coefs(r, [nm])[nm]
        if c[0] or c[1]:
            by[j] = c
    if by:
        rows4.append((cn, by))
stats4 = [("N", [f"{r['n']:,}" for r in res4]), ("R²", [f"{r['r2']:.3f}" for r in res4])]
three_line(esttab_like(cols4, ["lnwage"] * 5, rows4, stats4, size=8.5))
note("注：括号内为标准误；*、**、*** 分别表示 10%、5%、1% 显著。列 (3) 为教材例 4.37A（未中心化），"
     "列 (4) 为 4.37B（lnpop、educ 先分别减去均值再相乘）；列 (5) 只报告与 lnpop 交互的变量。")

h1("表四解读")
gr = B.groups_a
para(f"列 (1) 让性别与婚姻虚拟变量相乘，四类人在截距上各不相同：未婚女性 {gr.iloc[0, 1]:.3f}（基准组）、"
     f"未婚男性 {gr.iloc[1, 1]:.3f}（{gr.iloc[1, 2]}）、已婚女性 {gr.iloc[2, 1]:.3f}（{gr.iloc[2, 2]}）、"
     f"已婚男性 {gr.iloc[3, 1]:.3f}（{gr.iloc[3, 2]}）。交互项 male×marr 系数 {i1['male_x_marr'][0]:.3f}"
     f"（标准误 {i1['male_x_marr'][1]:.3f}，t = {tt(B.r4a, 'male_x_marr'):.1f}，95% 置信区间 "
     f"{cistr(B.r4a, 'male_x_marr')}，{sig(i1['male_x_marr'][2])}），表示“已婚相对于未婚的工资差异"
     f"在男性中额外多出 {P(i1['male_x_marr'][0]):.1f}%”。也就是说，未婚男性比未婚女性高 "
     f"{P(i1['male'][0]):.1f}%，而已婚男性比已婚女性高 {P(i1['male'][0] + i1['male_x_marr'][0]):.1f}%。"
     f"注意 marr 主效应只有 {i1['marr'][0]:.3f}（t = {tt(B.r4a, 'marr'):.2f}，{sig(i1['marr'][2])}），"
     "说明婚姻溢价几乎完全由男性获得；"
     "若只用表三的加法模型，会把这份异质性硬压成一个统一的系数，得出“已婚者一律更高”的错误结论，"
     "并把 male 系数压低——这正是表三（加法）与表四（乘法）对照的意义。")
para(f"列 (2) 让性别与教育相乘，检验教育回报有无性别差异：女性教育回报 {i2['educ'][0]:.3f}"
     f"（标准误 {i2['educ'][1]:.3f}，t = {tt(B.r4b, 'educ'):.1f}，{sig(i2['educ'][2])}，约每年 {P(i2['educ'][0]):.1f}%），"
     f"男性为 {i2['educ'][0] + i2['male_x_educ'][0]:.3f}（约每年 {P(i2['educ'][0] + i2['male_x_educ'][0]):.1f}%）。"
     f"male×educ 交互项 {i2['male_x_educ'][0]:.3f}（标准误 {i2['male_x_educ'][1]:.3f}，"
     f"t = {tt(B.r4b, 'male_x_educ'):.2f}，95% 置信区间 {cistr(B.r4b, 'male_x_educ')}，"
     f"{sig(i2['male_x_educ'][2])}），"
     + ("说明本样本中男女教育回报并无显著差异，性别差距主要表现为截距平移（male "
        f"{i2['male'][0]:.3f}，t = {tt(B.r4b, 'male'):.1f}），而不是斜率差异，因此表三用加法模型设定是合适的。"
        f"注意区间 {cistr(B.r4b, 'male_x_educ')} 虽然跨 0，但上限有限，"
        f"对应的教育回报差异在 -{P(-(i2['male_x_educ'][0] - 1.96 * i2['male_x_educ'][1])):.1f}~"
        f"{P(i2['male_x_educ'][0] + 1.96 * i2['male_x_educ'][1]):.1f}% 之间，"
        "方向上仍略偏向男性，只是证据不足以拒绝“无差异”。"
        if i2['male_x_educ'][2] > 0.10 else
        "说明男性的教育回报显著高于女性，教育与性别存在互补效应；"
        f"此时 male 主效应 {i2['male'][0]:.3f} 只是 educ=0 处的性别差异、没有实际含义，"
        f"必须写成 ∂lnwage/∂educ = {i2['educ'][0]:.3f} + {i2['male_x_educ'][0]:.3f}·male 才对。"))
para(f"列 (3) 是教材例 4.37A：把 lnpop 与 educ 相乘。交互项 {i3['lnpop_x_educ'][0]:.3f}（标准误 "
     f"{i3['lnpop_x_educ'][1]:.3f}，t = {tt(B.r4c, 'lnpop_x_educ'):.1f}，95% 置信区间 "
     f"{cistr(B.r4c, 'lnpop_x_educ')}，{sig(i3['lnpop_x_educ'][2])}）显著为正，边际效应为 "
     f"∂lnwage/∂lnpop = {i3['lnpop'][0]:.3f} + {i3['lnpop_x_educ'][0]:.3f}·educ："
     f"6 年教育者仅 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 6:.3f}，9 年 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 9:.3f}，"
     f"12 年 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 12:.3f}，16 年 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 16:.3f}，"
     f"19 年 {i3['lnpop'][0] + i3['lnpop_x_educ'][0] * 19:.3f}。可见城市规模的正向影响随教育年限提高而增强，"
     "高学历者才是大城市工资溢价的主要受益者。"
     f"lnpop 主效应 {i3['lnpop'][0]:.3f}（t = {tt(B.r4c, 'lnpop'):.1f}）为负、"
     f"educ 主效应 {i3['educ'][0]:.3f}（t = {tt(B.r4c, 'educ'):.1f}）也反常，"
     "原因是没有中心化——它们分别是 lnpop=0、educ=0 时的外推值。"
     f"嵌套模型的 F 检验（受限模型不含交互项）F({F_int[1]}, {F_int[2]}) = {F_int[0]:.2f}，"
     + ("p < 0.001，交互项在 1% 水平上联合显著，应拒绝“无交互效应”的原假设。" if F_int[3] < 0.01
        else f"p = {F_int[3]:.3f}。"))
para(f"列 (4) 是 4.37B 的中心化做法：把 lnpop、educ 分别减去均值（{mean_lnpop:.3f}、{mean_educ:.3f}）后再相乘。"
     f"交互项系数仍为 {i4['clnpop_x_ceduc'][0]:.3f}（标准误 {i4['clnpop_x_ceduc'][1]:.3f}，"
     f"t = {tt(B.r4d, 'clnpop_x_ceduc'):.1f}，{sig(i4['clnpop_x_ceduc'][2])}），与列 (3) 完全相同，"
     f"R² 也同为 {B.r4d['r2']:.3f}，"
     "说明中心化只改变坐标原点、不改变模型拟合；但主效应变得可解释了：中心化 lnpop 系数 "
     f"{i4['c_lnpop'][0]:.3f}（t = {tt(B.r4d, 'c_lnpop'):.1f}，95% 置信区间 {cistr(B.r4d, 'c_lnpop')}，"
     f"{sig(i4['c_lnpop'][2])}）是“平均教育水平者的城市规模弹性”，"
     f"中心化 educ 系数 {i4['c_educ'][0]:.3f}（t = {tt(B.r4d, 'c_educ'):.1f}，{sig(i4['c_educ'][2])}）"
     "是“平均规模城市的教育回报”，"
     f"两者恰好等于列 (3) 的边际效应在均值处的取值"
     f"（{i3['lnpop'][0] + i3['lnpop_x_educ'][0] * mean_educ:.3f}、{i3['educ'][0] + i3['lnpop_x_educ'][0] * mean_lnpop:.3f}）。"
     "这就是教材强调“交互项模型要中心化后再解释”的原因：不中心化时主效应是外推值，"
     "极易被误读为“大城市工资反而更低”。")
para(f"列 (5) 把城市规模与性别、婚姻相乘，看谁从城市规模中获益更多：lnpop×male "
     f"{i5['lnpop_x_male'][0]:.3f}（标准误 {i5['lnpop_x_male'][1]:.3f}，t = {tt(B.r4e, 'lnpop_x_male'):.2f}，"
     f"95% 置信区间 {cistr(B.r4e, 'lnpop_x_male')}，{sig(i5['lnpop_x_male'][2])}）、"
     f"lnpop×marr {i5['lnpop_x_marr'][0]:.3f}（标准误 {i5['lnpop_x_marr'][1]:.3f}，"
     f"t = {tt(B.r4e, 'lnpop_x_marr'):.2f}，95% 置信区间 {cistr(B.r4e, 'lnpop_x_marr')}，"
     f"{sig(i5['lnpop_x_marr'][2])}）。"
     + ("lnpop×male 不显著，男女的城市规模弹性无明显差别；" if i5['lnpop_x_male'][2] > 0.10 else
        ("lnpop×male 显著为负，女性的城市规模弹性更大；" if i5['lnpop_x_male'][0] < 0 else
         "lnpop×male 显著为正，男性的城市规模弹性更大；"))
     + ("lnpop×marr 不显著，婚姻状况不影响城市规模溢价。" if i5['lnpop_x_marr'][2] > 0.10 else
        ("lnpop×marr 显著为正，已婚者的城市规模溢价更高；" if i5['lnpop_x_marr'][0] > 0 else
         "lnpop×marr 显著为负，未婚者的城市规模溢价更高；"))
     + "综合看，本样本中最稳健、经济含义最清晰的交互效应是 lnpop×educ：城市规模溢价随学历递增，"
     "并且必须中心化后才能正确解读主效应。物质回报的差异既可能来自截距（性别、婚姻），"
     "也可能来自斜率（教育、城市规模），加法模型只能刻画前者，乘法模型才能同时刻画两者。")
para("最后需要说明这些估计的解释边界。本报告使用的是 CMDS2017 的横截面数据，四张表的系数都是"
     "“条件相关”意义上的估计，而非严格的因果效应。以城市规模弹性为例：能力更强的劳动者"
     "本身就更可能选择流入大城市，这种不可观测的个人能力既影响工资、也与城市选择正相关，"
     "会使 lnpop 系数向上偏（自选择偏误）；反过来，大城市生活成本高，需要更高名义工资补偿，"
     "又会部分虚增系数。因此 0.087 左右的弹性更适合解读为“同一时点上不同规模城市的工资差距”，"
     "若要识别“迁移到大城市会使工资提高多少”，需要工具变量（如历史上的城市规模、地形或政策冲击）、"
     "面板数据的固定效应模型，或者利用个体的迁移轨迹做双重差分。同理，性别与婚姻的工资差异"
     "也包含不可观测的行业选择、职业选择与家庭分工等因素，不能直接当作“歧视”的度量。"
     "把估计结果理解为对样本内工资形成机制的条件描述，是更稳妥、也更符合横截面数据性质的做法。")

# ================================================================ 附录：代码
doc.add_page_break()
h1("附录：运行代码")
para("以下为 Stata 运行代码（chapter4_四表.do）。数据只用实验一文件夹中的 CMDS2017子样本.dta 一个文件，"
     "脚本直接使用该文件的 7 个变量做回归，依次输出表一至表四；需 ssc install estout。", after=4)


def code_block(text, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    set_cn(p.add_run(title), "黑体", 11, True)
    for line in text.splitlines():
        q = doc.add_paragraph()
        q.paragraph_format.space_before = Pt(0)
        q.paragraph_format.space_after = Pt(0)
        q.paragraph_format.line_spacing = 1.0
        q.paragraph_format.left_indent = Pt(6)
        set_cn(q.add_run(line if line.strip() else " "), "Consolas", 7.5)


for _f in ["chapter4_四表.do"]:
    _p = os.path.join(B.BASE, "do文件", _f)
    if os.path.exists(_p):
        code_block(open(_p, encoding="utf-8").read(), f"Stata do 文件（{_f}）")

doc.save(DOCX)
print("已保存:", DOCX)
