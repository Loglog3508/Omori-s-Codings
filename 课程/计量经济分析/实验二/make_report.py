# -*- coding: utf-8 -*-
r"""
生成 实验二 交付 Word：
  封面 → 一、实验目的与数据 → 二、第11页 4.1 函数形式 → 三、第17页 题1 4.3.2 虚拟×定量
  → 四、第17页 题1 4.3.3 定量×定量 → 五、第17页 题2 4.5 Stata 应用（4.37A/4.37B）
  → 六、结论 → 附录：运行代码
运行： python 实验二\make_report.py
"""
import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

BASE = r"C:\Users\omori\Omori-s-Codings\课程\计量经济分析"
EXP2 = os.path.join(BASE, "实验二")
CLASS_NAME = "大数据242"
STUDENT_NAME = "洪翼雄"
STUDENT_ID = "2407150229"
DOCX = os.path.join(EXP2, f"{CLASS_NAME}-{STUDENT_NAME}-{STUDENT_ID}.docx")

E = 2.718281828459045


def pct(b):
    """半弹性 b 的精确百分比变化：100*(exp(b)-1)"""
    return 100 * (E ** b - 1)


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


def set_cn(run, font="宋体", size=10.5, bold=False, ea=None):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea or font)


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
    p.paragraph_format.keep_with_next = True   # 防止标题孤立在页底
    set_cn(p.add_run(text), "黑体", 13, True)
    return p


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    set_cn(p.add_run(text), "黑体", 11, True)
    return p


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
    p.paragraph_format.keep_with_next = True   # 表题与表格同页
    set_cn(p.add_run(text), "黑体", 10.5, True)
    return p


def note(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    set_cn(p.add_run(text), "楷体", 9)


def _set_border(el, edge, sz):
    tag = "w:" + edge
    for e in el.findall(qn(tag)):
        el.remove(e)
    b = el.makeelement(qn(tag), {qn("w:val"): "single", qn("w:sz"): str(sz),
                                 qn("w:space"): "0", qn("w:color"): "000000"})
    el.append(b)


def _drop_table_borders(tbl):
    """清掉表格级 tblBorders：LibreOffice 会据此画出整张网格线，故三线表一律改用单元格级边框。"""
    tblPr = tbl._tbl.tblPr
    for e in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(e)


def _cell_borders(cell, top=None, bottom=None):
    """单元格级 tcBorders：需要的横线画黑色，其余边一律画 2 号白线。

    注意：不能用 w:val="nil"/"none" 隐藏边框——LibreOffice 与 Word 在部分情况下仍会
    按默认表格样式画出浅灰网格线，用白色实线覆盖才是稳妥做法。
    """
    tcPr = cell._tc.get_or_add_tcPr()
    for e in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(e)
    bd = tcPr.makeelement(qn("w:tcBorders"), {})
    for edge, sz in (("top", top), ("left", None), ("bottom", bottom), ("right", None)):
        b = bd.makeelement(qn("w:" + edge), {
            qn("w:val"): "single",
            qn("w:sz"): str(sz if sz else 2),
            qn("w:space"): "0",
            qn("w:color"): "000000" if sz else "FFFFFF"})
        bd.append(b)
    tcPr.append(bd)


def _row_flag(row, tag):
    trPr = row._tr.get_or_add_trPr()
    for e in trPr.findall(qn("w:" + tag)):
        trPr.remove(e)
    trPr.append(trPr.makeelement(qn("w:" + tag), {}))


def three_line(t, nhead=1, col_rule=True, top_sz=12, mid_sz=6, bot_sz=12, keep_last=True):
    _drop_table_borders(t)
    nrows = len(t.rows)
    for i, row in enumerate(t.rows):
        for cell in row.cells:
            _cell_borders(cell,
                          top=top_sz if i == 0 else None,
                          bottom=(mid_sz if (col_rule and i == nhead - 1)
                                  else (bot_sz if i == nrows - 1 else None)))
        _row_flag(row, "cantSplit")          # 单元格内容不跨页断开
        if i < nhead and nrows > 15:
            _row_flag(row, "tblHeader")      # 长表跨页时重复表头
    if keep_last:                            # 表末行与紧跟的表注保持同页
        for _row in t.rows[(0 if nrows <= 10 else nrows - 1):]:
            for _c in _row.cells:
                for _p in _c.paragraphs:
                    _p.paragraph_format.keep_with_next = True
    return t


def _tight(p):
    """表格单元格内段落：单倍行距 + 无段前段后，行高更紧凑。"""
    pf = p.paragraph_format
    pf.line_spacing = 1.0
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)


def add_table(df, size=9, header=True):
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
            _tight(p)
            set_cn(p.add_run(str(c)), "黑体", size, True)
        off = 1
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            v = df.iat[i, j]
            cell = t.cell(i + off, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and df.shape[1] > 2) else WD_ALIGN_PARAGRAPH.CENTER
            _tight(p)
            set_cn(p.add_run("" if (v is None or (isinstance(v, float) and v != v)) else str(v)),
                   "宋体", size, False)
    return t


def _keep_next_row(row):
    """让整行与下一行保持在同一页（防止系数行与标准误行被分页拆开）。"""
    for cell in row.cells:
        for p in cell.paragraphs:
            p.paragraph_format.keep_with_next = True


def esttab_like(cols_titles, depvars, rows, stats, size=9, extra_head=None):
    """rows: [(变量名, {列号: (系数, 标准误)})]；stats: [(行名, [值...])]"""
    data = [[c for c in [""] + list(cols_titles)], [c for c in [""] + list(depvars)]]
    if extra_head:
        data.append([""] + list(extra_head))
    for nm, by_col in rows:
        data.append([nm] + [by_col.get(j, ("", ""))[0] for j in range(len(cols_titles))])
        data.append([""] + [by_col.get(j, ("", ""))[1] for j in range(len(cols_titles))])
    for nm, vals in stats:
        data.append([nm] + list(vals))
    df = pd.DataFrame([[str(v) for v in row] for row in data]).astype(object)
    nhead = 3 if extra_head else 2
    t = three_line(add_table(df, size=size, header=False), nhead=nhead, col_rule=False)
    nrows = len(t.rows)
    for i in range(nhead, nrows - 1, 2):   # 系数行 → 与紧随的标准误行同页
        _keep_next_row(t.rows[i])
    for i in range(nhead):                 # 表头各行也保持连续
        _keep_next_row(t.rows[i])
    return t


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def sig(p):
    return ("在 1% 的水平上显著" if p < 0.01 else "在 5% 的水平上显著" if p < 0.05
            else "在 10% 的水平上显著" if p < 0.10 else "不显著（|t| 未达 10% 临界值）")


def cell(b, se, p, nd=4):
    return (f"{b:.{nd}f}{star(p)}", f"({se:.{nd}f})")


# ================================================================ 封面
para("计量经济分析", size=20, bold=True, align="center", indent=False, font="黑体", after=8)
for _ in range(2):
    doc.add_paragraph()
para("进一步讨论：函数形式的确定与交互项", size=15, bold=True, align="center",
     indent=False, font="黑体", after=6)
para("——实验二：教材第 11 页（4.1 函数形式）与第 17 页（4.3.2、4.3.3、4.5）", size=11,
     align="center", indent=False)
for _ in range(3):
    doc.add_paragraph()
three_line(add_table(pd.DataFrame([
    ["班级", CLASS_NAME],
    ["姓名", STUDENT_NAME],
    ["学号", STUDENT_ID],
    ["数据", r"演示数据\wage_chap4.dta（13 个变量）"],
    ["样本", "N = 14,757（129 个城市、20 个行业、8 个职业）"],
    ["软件", "Stata 18（StataMP-64）；do 文件见文末"],
    ["题目", "4.1 函数形式；4.3.2 虚拟×定量；4.3.3 定量×定量；4.5 Stata 应用"],
], columns=["项目", "内容"]), size=10))
doc.add_page_break()

# ================================================================ 一、实验目的与数据
h1("一、实验目的与数据说明")
para("本实验以教材《回归模型的进一步议题》第 11 页与第 17 页为依据，围绕“函数形式如何确定”与"
     "“交互项如何设定和解读”两个问题展开。第 11 页是 4.1 节“函数形式的确定”，"
     "给出对数—线性、线性—对数、双对数、多项式四类设定及其系数的经济含义；"
     "第 17 页对应两个题目：题 1 是 4.3 节“模型中的交互项与偏效应”，包括 4.3.2 节虚拟变量和"
     "定量变量的交互（式 4.23—4.28）与 4.3.3 节定量变量和定量变量的交互（式 4.29—4.33）；"
     "题 2 是 4.5 节“Stata 应用”，用例 4.37 的式 4.37A、4.37B 演示 reghdfe 吸收高维固定效应、"
     "margins 求偏效应、center 中心化三步。")
para("数据为 wage_chap4.dta，共 14,757 个观测、13 个变量，全部无缺失值。变量与教材一致："
     "lnwage 为月工资的自然对数（原数据未提供水平值 wage，本实验按 wage = exp(lnwage) 还原），"
     "lnpop 为城市人口规模的自然对数，educ 为受教育年限，exp 为工作经验（年）、exp2 为其平方，"
     "male、marr、luohu 分别为男性、已婚、本地户口虚拟变量，age 为年龄，city_time 为本地居住时间，"
     "health 为健康状况（1 差、2 一般、3 好），hangye 为行业（20 类），zhiye 为职业（8 类）。"
     "与实验一相比，wage_chap4.dta 的 male、educ、exp、exp2、marr、lnpop、lnwage 七个变量"
     "与 CMDS2017 子样本逐行一致，实验一的结论可原样沿用；额外提供的 age、city_time、hangye、"
     "zhiye、health 正是 4.5 节例 4.37 控制固定效应与稳健性检查所必需的。")
caption("表 1：变量的描述性统计")
t1 = pd.DataFrame([
    ["lnwage", "14,757", "8.277", "0.517", "6.908", "10.597"],
    ["wage（还原）", "14,757", "4573.842", "3172.498", "1000", "40000"],
    ["lnpop", "14,757", "6.596", "0.853", "3.218", "8.031"],
    ["educ", "14,757", "11.425", "3.376", "0", "19"],
    ["exp", "14,757", "16.340", "10.967", "0", "59"],
    ["exp2", "14,757", "387.243", "472.428", "0", "3481"],
    ["age", "14,757", "33.765", "9.350", "16", "65"],
    ["male", "14,757", "0.539", "0.498", "0", "1"],
    ["marr", "14,757", "0.728", "0.445", "0", "1"],
    ["luohu（是=1）", "14,757", "0.454", "0.498", "0", "1"],
    ["city_time", "14,757", "5.453", "5.515", "0", "57"],
    ["health", "14,757", "2.854", "0.375", "1", "3"],
], columns=["VarName", "Obs", "Mean", "SD", "Min", "Max"])
three_line(add_table(t1))
note("注：数据为 演示数据\\wage_chap4.dta，N = 14,757。lnwage、lnpop 已在对数尺度上；"
     "wage = exp(lnwage) 为还原的月工资（元）；luohu 已转 0/1 虚拟变量（本地户口 = 1，占 45.4%）。"
     "health 取值 1/2/3 的样本量分别为 117、1,927、12,713；hangye、zhiye 为多类别编码变量，未列入表内。")
para("表 1 显示：月工资还原后均值约 4,574 元、范围 1,000~40,000 元，工资已做过清理，"
     "取对数后系数可按百分比变化解读；lnpop 标准差 0.853，还原后城市人口跨越两个数量级，"
     "变异性足以识别城市规模效应；educ 均值 11.425 年、介于 0~19 年，恰好是高中毕业（12 年）前后，"
     "后文中心化时要用的 educ 均值即 11.4250；male 均值 0.539、marr 均值 0.728，"
     "两类样本量都很充足。exp2 的均值与标准差远大于 exp（平方放大了量级），"
     "因此回归中经验平方项的系数必然在 10⁻³~10⁻⁴ 量级，其含义不能直接按“每年变化”解读，"
     "而要结合转折点 −β₁/(2β₂) 说明。")

# ================================================================ 二、第 11 页 4.1
h1("二、第 11 页：4.1 函数形式的确定")
para("4.1 节的核心问题是：被解释变量与解释变量究竟该取水平值还是对数？不同的组合对应不同的"
     "经济含义，也对应不同的系数解读规则。教材给出四类设定：线性—线性 Y = β₀ + β₁X + ε（式 4.1），"
     "对数—线性（半对数）lnY = β₀ + β₁X + ε（式 4.2—4.7），"
     "线性—对数 Y = β₀ + β₁lnX + ε（式 4.9—4.11），双对数 lnY = β₀ + β₁lnX + ε（式 4.12—4.14），"
     "以及多项式 Y = β₀ + β₁X + β₂X² + ε（式 4.15—4.16）。下面逐类估计并给出系数解读。")

h2("2.1 对数—线性模型：教育回报率")
para("把被解释变量取对数、解释变量保留水平值，得到半对数模型：", after=2)
form("lnwage = β₀ + β₁·educ + ε                                    （式 4.2）")
form("β₁ = dlnwage/deduc，Δlnwage ≈ β₁·Δeduc                        （式 4.3、4.4）")
form("精确百分比变化 = 100·[exp(β₁) − 1] %                          （式 4.5、4.6）")
para("估计结果见表 2 第 (2) 列：educ 系数 0.0512，标准误 0.0012，在 1% 水平显著，R² = 0.112。"
     "按式 4.4 的近似法，每多受一年教育月工资约高 5.12%；按式 4.6 的精确公式，"
     "100×(e^0.0512−1)% = 5.25%。两者相差 0.13 个百分点，正是教材强调“半弹性较大时近似式会低估”的情形。"
     "作为对照，表 2 第 (1) 列把 wage 放在水平上做线性—线性回归，educ 系数 292.53 元"
     "（标准误 7.35），即每年多读一年书月工资高约 293 元；但模型 R² 只有 0.097，低于半对数模型的 0.112，"
     "而且线性模型隐含“任何教育水平下每多一年教育的绝对工资增幅都相同”的强假设，"
     "与工资随教育递增的百分比增长规律不符，因此研究教育回报率时半对数设定更合适。")

h2("2.2 线性—对数模型与双对数模型：城市规模的作用")
para("把解释变量取对数、被解释变量保留水平值：", after=2)
form("wage = β₀ + β₁·lnpop + ε                                     （式 4.9）")
form("β₁ = dY/dlnX，ΔY ≈ β₁·(ΔX/X)，X 变动 1% 时 Y 变动 0.01·β₁   （式 4.10、4.11）")
para("估计得到 lnpop 系数 705.49（标准误 30.07，在 1% 水平显著），即城市人口每多 1%，"
     "月工资约高 7.05 元。但常数项 −79.74 不显著（t = −0.40，p = 0.690），"
     "说明线性—对数设定在解释变量很小时会给出没有意义的负工资预测。")
para("再让被解释变量也取对数，得到双对数模型：", after=2)
form("lnwage = β₀ + β₁·lnpop + ε                                   （式 4.12）")
form("β₁ = dlnY/dlnX，即弹性                                        （式 4.13、4.14）")
para("估计得到 lnwage = 7.524 + 0.114·lnpop（系数标准误 0.0049，R² = 0.035），"
     "城市规模弹性 0.114，即城市人口每增加 1% 工资高约 0.114%、每增加 10% 工资高约 1.14%。"
     "这个结果与教材式 4.14 给出的 lnwage = 7.53 + 0.114·lnpop 精确吻合到小数点后三位，"
     "说明用 wage_chap4.dta 可以完整复现教材结果。双对数模型的优点在于："
     "系数与量纲无关、可以直接读作弹性；不会出现负的预测值；R² 也口径可比。"
     "信息准则的对比同样支持双对数：线性—对数模型 AIC = 279290.9、BIC = 279306.1，"
     "双对数模型 AIC = 21889.99、BIC = 21905.19，后者大幅更优——"
     "当然两个模型的被解释变量不同（wage 与 lnwage），严格说信息准则不能直接跨被解释变量比较，"
     "这里只作为量级上的旁证，真正的依据是弹性的经济含义与避免负预测值。")

h2("2.3 多项式模型：工资—经验曲线")
para("把工作经验及其平方同时放进模型：", after=2)
form("lnwage = β₀ + β₁·exp + β₂·exp² + ε                           （式 4.15）")
form("∂lnwage/∂exp = β₁ + 2·β₂·exp，转折点 X* = −β₁/(2β₂)          （式 4.16）")
para("估计得到 lnwage = 8.157 + 0.0268·exp − 0.00082·exp²，"
     "一次项系数 0.02675（标准误 0.00128）显著为正、二次项系数 −0.000818"
     "（标准误 0.0000297）显著为负，R² = 0.070，说明工资随经验先升后降，呈现倒 U 形。"
     "按式 4.16 计算转折点：X* = −0.02675/(2×(−0.000818)) = 16.35 年，"
     "即工作经验约 16 年后月工资达到峰值，之后开始下降。"
     "教材用 wage 数据得到的转折点约 18.6 年，两者差异来自样本不同，但倒 U 形的形状完全一致。")
para("作为反例，若只放线性经验项，回归得到 exp 系数 −0.00694（标准误 0.00038），"
     "符号与实际经验规律相反——原因正是遗漏了平方项：工作经验的边际效应随年限递减，"
     "线性设定只能用一个平均斜率概括，被后期经验的负效应主导后整体变成负值。"
     "对平方项做 F 检验：F(1, 14754) = 760.31，p < 0.001；用 nestreg 做嵌套模型的增量检验，"
     "加入 exp² 后 F(1, 14754) = 760.31，R² 由 0.021 提高到 0.070，增量 R² = 0.0479。"
     "可见平方项绝不多余，多项式设定是必要的。")

h2("2.4 四种设定的选择")
caption("表 2：四种函数形式的估计结果")
rows2 = [
    ("lnpop", {0: ("—", ""), 1: ("—", ""), 2: ("705.49***", "(30.07)"),
               3: ("0.1141***", "(0.0049)"), 4: ("0.0817***", "(0.0047)")}),
    ("educ", {0: ("292.53***", "(7.35)"), 1: ("0.0512***", "(0.0012)"),
              2: ("—", ""), 3: ("—", ""), 4: ("0.0476***", "(0.0012)")}),
    ("exp", {0: ("—", ""), 1: ("—", ""), 2: ("—", ""), 3: ("—", ""),
             4: ("0.0268***", "(0.0013)")}),
    ("exp2", {0: ("—", ""), 1: ("—", ""), 2: ("—", ""), 3: ("—", ""),
              4: ("−0.00082***", "(0.00003)")}),
    ("_cons", {0: ("1231.65***", "(87.57)"), 1: ("7.6923***", "(0.0142)"),
               2: ("−79.74", "(199.97)"), 3: ("7.5242***", "(0.0326)"),
               4: ("8.1566***", "(0.0112)")}),
]
stats2 = [("N", ["14,757"] * 5), ("R²", ["0.097", "0.112", "0.036", "0.035", "0.070"])]
three_line(esttab_like(
    ["(1)", "(2)", "(3)", "(4)", "(5)"],
    ["wage", "lnwage", "wage", "lnwage", "lnwage"],
    rows2, stats2, size=9,
    extra_head=["线性—线性", "对数—线性", "线性—对数", "双对数", "多项式"]))
note("注：括号内为标准误；*、**、*** 分别表示在 10%、5%、1% 的水平上显著。"
     "列 (5) 的被解释变量为 lnwage，解释变量为 exp 与 exp²；"
     "列 (1)(3) 的被解释变量为还原的水平工资 wage。")
para("四类设定的选择遵循教材 4.1 节给出的四条建议。"
     "第一，看被解释变量的取值范围与经济约束：工资必须为正，对数设定天然满足，"
     "线性—对数模型的常数项为负、在小城市会预测出负工资，因此不予采用。"
     "第二，看系数的经济含义是否切题：研究教育回报率、城市规模溢价时，"
     "关注的正是“百分比变化”，半弹性与双对数设定直接把系数读作百分比，最为自然；"
     "水平值的系数（如 292.53 元）则依赖工资的量纲，不便横向比较。"
     "第三，看解释力与信息准则：同样解释 wage 的水平值时，线性—线性 R² = 0.097 高于线性—对数的 0.036；"
     "同样解释 lnwage 时，半对数 R² = 0.112 高于双对数的 0.035，说明教育比城市规模更能解释工资差异。"
     "第四，看是否需要刻画非线性：经验对工资的影响明显倒 U 形，线性项符号会反号，"
     "必须引入平方项，此时转折点 −β₁/(2β₂) 成为关键结果。"
     "综合起来，本实验后续统一采用“被解释变量取对数、解释变量按经济含义取水平或对数、"
     "必要时加平方项”的设定，即 lnwage 为被解释变量，lnpop、educ 为解释变量，经验用 exp 与 exp² 刻画。")

# ================================================================ 三、4.3.2
h1("三、第 17 页题 1（上）：4.3.2 虚拟变量和定量变量的交互")
para("4.3.2 节讨论一个虚拟变量与一个定量变量相乘的模型。以性别与教育为例：", after=2)
form("lnwage = β₀ + β₁·male + β₂·educ + β₃·(male×educ) + ε        （式 4.23）")
form("∂lnwage/∂educ = β₂ + β₃·male                                 （式 4.24）")
form("∂lnwage/∂male = β₁ + β₃·educ                                 （式 4.25）")
para("式 4.23 中，β₁ 不再是“男女工资差异”，β₂ 也不再是“教育回报率”，"
     "而是交互项为 0 时的截距与斜率：β₁ = 女性的截距差、β₂ + β₃ 才是男性每多一年教育的回报。"
     "式 4.25 表明性别差异本身也随教育年限变化，这正是交互项的用处——"
     "它允许两组的斜率不同，而不仅是截距不同（加法模型只允许截距不同）。")

h2("3.1 不设交互项与设交互项的对比")
para("先看只含主效应的加法模型（表 3 第 (1) 列）：lnwage = 7.554 + 0.2375·male + 0.0521·educ，"
     "male 系数 0.2375（标准误 0.0078，1% 水平显著），按精确公式换算男性比女性高约 "
     f"{pct(0.2375):.1f}%，R² = 0.164。"
     "再看式 4.23 的乘法模型（表 3 第 (2) 列）：male 系数 0.19461（标准误 0.02751）、"
     "educ 系数 0.05022（标准误 0.00164）、male×educ 系数 0.010226，"
     "其中 male×educ 的 t 统计量约 5.6，在 1% 水平显著，R² 从 0.1640 微升到 0.1641。")
caption("表 3：虚拟变量与定量变量的交互（被解释变量：lnwage）")
rows3 = [
    ("male", {0: ("0.2375***", "(0.0078)"), 1: ("0.1946***", "(0.0275)"),
              2: ("0.2375***", "(0.0078)")}),
    ("educ", {0: ("0.0521***", "(0.0012)"), 1: ("0.0502***", "(0.0016)"),
              2: ("0.0502***", "(0.0016)")}),
    ("male×educ", {1: ("0.0102***", "(0.0026)"), 2: ("—", "")}),
    ("male×educ（中心化）", {2: ("0.0102***", "(0.0026)")}),
    ("_cons", {0: ("7.5537***", "(0.0145)"), 1: ("7.5755***", "(0.0197)"),
               2: ("8.1492***", "(0.0057)")}),
]
stats3 = [("N", ["14,757"] * 3), ("R²", ["0.1640", "0.1641", "0.1641"])]
three_line(esttab_like(
    ["(1) 加法", "(2) 乘法 式4.23", "(3) 中心化 式4.26"],
    ["lnwage"] * 3, rows3, stats3, size=8.5))
note("注：括号内为标准误；*、**、*** 分别表示 10%、5%、1% 显著。"
     "列 (2) 中 educ 系数为男性与女性的共同基准，男性教育回报为 0.0502 + 0.0102 = 0.0604；"
     "列 (3) 中 c_educ = educ − 11.4250，故 male 系数 0.2375 即“教育均值处的性别工资差异”。")

h2("3.2 系数的正确解读：偏效应随对方变化")
para("式 4.25 的偏效应 ∂lnwage/∂male = 0.19461 + 0.010226·educ 随教育年限递增，逐点计算如下：")
caption("表 4：不同教育年限下的性别工资差异（式 4.25 的偏效应）")
t4 = pd.DataFrame([
    ["0（未上学）", "0.1946", "21.5"],
    ["6（小学）", "0.2171", "24.3"],
    ["9（初中）", "0.2284", "25.7"],
    ["12（高中）", "0.2396", "27.1"],
    ["15（大专）", "0.2509", "28.5"],
    ["16（本科）", "0.2546", "29.0"],
    ["19（研究生）", "0.2659", "30.5"],
], columns=["受教育年限", "∂lnwage/∂male", "折算百分比（%）"])
three_line(add_table(t4))
note("注：折算百分比按精确公式 100×[exp(偏效应)−1]% 计算；"
     "偏效应 = β₁ + β₃·educ = 0.19461 + 0.010226·educ。男性教育回报为 0.0604，女性为 0.0502。")
para("表 4 揭示了交互项的经济含义：教育程度越高，男女工资差距越大。"
     "未上学者的性别差异只有 21.5%，本科毕业生达 29.0%，研究生达 30.5%；"
     "换个角度看，男性每多受一年教育月工资高约 6.23%，女性只有 5.15%，"
     "男性的教育回报率比女性高约 1.08 个百分点。"
     "若用加法模型（表 3 第 (1) 列），只能得到“男性一律高 23.7%”这个平均数，"
     "既会高估低学历者的性别差距，又会低估高学历者的差距，掩盖了异质性。")

h2("3.3 中心化：让主效应变得可解释")
para("式 4.23 中 male 的系数 0.19461 是 educ = 0 处的性别差异，"
     "对“未上学者”这个极端子群成立，不能直接当作一般性的性别差距。"
     "教材的处理办法是中心化：把 educ 换成偏离均值的 educ − educ̄。", after=2)
form("lnwage = α₀ + α₁·male + α₂·(educ − educ̄) + α₃·male×(educ − educ̄) + ε   （式 4.26）")
form("∂lnwage/∂male = α₁ + α₃·(educ − educ̄)                        （式 4.28）")
para("本样本 educ̄ = 11.4250。用 center 命令或手工相减后重新估计（表 3 第 (3) 列）："
     "male 系数 0.2375（标准误 0.0078），正是“平均教育水平处的性别工资差异”折算约 "
     f"{pct(0.2375):.1f}%；交互项系数仍为 0.0102，与列 (2) 完全相同；R² 也不变（0.1641），"
     "说明中心化只是换了一个坐标原点，模型拟合与交互效应的大小丝毫未变。"
     "教材用同一数据在 4.3.2 节末尾指出：male 系数由未中心化的不显著水平变为在均值处的 23.7%，"
     "本实验得到的 23.7% 与之完全一致。"
     "用 Stata 的 margins, dydx(male) atmeans 也可以直接得到均值处的这个数，"
     "而 margins, dydx(1.male) atmeans 还会给出 factor 变量的离散变化（0→1）。")

# ================================================================ 四、4.3.3
h1("四、第 17 页题 1（下）：4.3.3 定量变量和定量变量的交互")
para("4.3.3 节把交互项从“虚拟×定量”推广到“定量×定量”。以城市规模与教育为例：", after=2)
form("lnwage = β₀ + β₁·lnpop + β₂·educ + β₃·(lnpop×educ) + ε      （式 4.29）")
form("∂lnwage/∂lnpop = β₁ + β₃·educ                                （式 4.30）")
form("∂lnwage/∂educ = β₂ + β₃·lnpop                                 （式 4.30）")
para("这里的解释比虚拟变量情形更微妙：两个解释变量的偏效应都随对方变化。"
     "β₁ 不再是城市规模弹性，而是 educ = 0（从未上学）时的弹性；"
     "β₂ 也不是教育回报率，而是 lnpop = 0（人口为 1 的城市）时的教育回报——"
     "都是严重外推、没有实际经济意义的数值。"
     "把 educ 与 lnpop 分别中心化后再相乘，可以消除这个问题：", after=2)
form("lnwage = α₀ + α₁·(lnpop−lnpop̄) + α₂·(educ−educ̄) + α₃·(lnpop−lnpop̄)(educ−educ̄) + ε （式 4.31、4.32）")
form("偏效应 = α₁ + α₃·(X₂ − X̄₂)，在均值处即 α₁                      （式 4.33）")

caption("表 5：定量变量与定量变量的交互（被解释变量：lnwage）")
rows5 = [
    ("lnpop", {0: ("0.0817***", "(0.0047)"), 1: ("−0.1661***", "(0.0153)"),
               2: ("—", ""), 3: ("0.0859***", "(0.0047)")}),
    ("educ", {0: ("0.0476***", "(0.0012)"), 1: ("−0.0982***", "(0.0087)"),
              2: ("—", ""), 3: ("0.0473***", "(0.0012)")}),
    ("lnpop×educ", {1: ("0.0221***", "(0.0013)"), 2: ("—", ""), 3: ("—", "")}),
    ("c_lnpop×c_educ", {2: ("0.0221***", "(0.0013)"), 3: ("—", "")}),
    ("_cons", {0: ("7.1936***", "(0.0321)"), 1: ("8.8217***", "(0.1011)"),
               2: ("8.2661***", "(0.0040)"), 3: ("7.6997***", "(0.0312)")}),
]
stats5 = [("N", ["14,757"] * 4), ("R²", ["0.1293", "0.1459", "0.1459", "0.1459"])]
three_line(esttab_like(
    ["(1) 主效应", "(2) 式4.29", "(3) 手工中心化 式4.31", "(4) 因子写法 式4.32"],
    ["lnwage"] * 4, rows5, stats5, size=8.5))
note("注：括号内为标准误；*、**、*** 分别表示 10%、5%、1% 显著。"
     "列 (3) 的 c_lnpop = lnpop − 6.5962、c_educ = educ − 11.4250；"
     "列 (4) 用 c.lnpop##c.educ 因子写法，把 educ 的中心化值当作连续变量输入。")

h2("4.1 交互项显著，且主效应不可直接解读")
para("表 5 第 (1) 列是只含主效应的模型：lnpop 0.0817、educ 0.0476，R² = 0.1293。"
     "第 (2) 列加入 lnpop×educ 交互项，交互项系数 0.0221（标准误 0.0013），t ≈ 16.95，"
     "在 1% 水平显著，R² 升至 0.1459。此时 lnpop 系数变为 −0.1661（标准误 0.0153）、"
     "educ 系数变为 −0.0982（标准误 0.0087），两个主效应都变成负值——"
     "这不能解读为“大城市工资更低”，"
     "而是因为它们是 educ = 0、lnpop = 0 时的外推值，该点之外没有观测。"
     "按式 4.30 逐点算偏效应，见表 6。")

caption("表 6：不同教育年限下的城市规模工资弹性（式 4.30 的偏效应）")
t6 = pd.DataFrame([
    ["6（小学）", "−0.0338", "−3.32"],
    ["9（初中）", "0.0324", "3.29"],
    ["12（高中）", "0.0986", "10.36"],
    ["15（大专）", "0.1647", "17.90"],
    ["16（本科）", "0.1868", "20.54"],
    ["19（研究生）", "0.2529", "28.78"],
], columns=["受教育年限", "∂lnwage/∂lnpop", "城市人口 +1% 时工资 +（%）"])
three_line(add_table(t6))
note("注：偏效应 = β₁ + β₃·educ = −0.16607 + 0.022052·educ；"
     "百分比按精确公式 100×[exp(偏效应)−1]% 计算。数据不含固定效应与个体控制变量。")
para("表 6 给出了清晰的经济结论：城市规模溢价随教育程度单调上升。"
     "小学学历者的城市规模弹性几乎为 0（甚至微负），高中约 0.099，本科达 0.187，研究生达 0.253。"
     "换句话说，城市人口多 10%，研究生学历者的月工资约高 2.5%，"
     "而小学学历者几乎没有变化——高学历者才是大城市工资溢价的受益者。"
     "这正是教材第 17 页例 4.37 要说明的核心命题。"
     "反过来看式 4.30 的另一个偏效应 ∂lnwage/∂educ = β₂ + β₃·lnpop："
     "lnpop = 4（约 55 人）时为 −0.0100，6（约 403 人）时为 0.0341，8（约 2,981 人）时为 0.0782，"
     "即城市越大、教育回报率越高，与上表的结论等价、互为镜像。")

h2("4.2 中心化的作用与式 4.33")
para("表 5 第 (3) 列把两个变量都中心化后相乘（手工生成 c_lnpop、c_educ 与二者乘积），"
     "第 (4) 列用 c.lnpop##c.educ 因子写法。两列结果一致：交互项系数仍为 0.0221，"
     "与第 (2) 列完全相同，R² 也同为 0.1459，可见中心化不改变交互效应与拟合优度。"
     "但主效应变得可解释了：lnpop 系数 0.0859（标准误 0.0047）是“平均教育水平（11.425 年）劳动者的城市规模弹性”，"
     "educ 系数 0.0473（标准误 0.0012）是“平均规模城市的教育回报”。"
     "按式 4.33 验证：β₁ + β₃·educ̄ = −0.16607 + 0.022052×11.425 = 0.0859，"
     "β₂ + β₃·lnpop̄ = −0.098207 + 0.022052×6.596 = 0.0473，与中心化后的主效应完全吻合。"
     "这验证了教材的说法：中心化后，主效应恰好等于偏效应在对方均值处的取值。")

# ================================================================ 五、4.5 Stata 应用
h1("五、第 17 页题 2：4.5 Stata 应用（例 4.37）")
para("4.5 节用例 4.37 演示交互项模型在 Stata 中的完整实现。模型为：", after=2)
form("lnwage = β₀ + β₁·lnpop + β₂·educ + β₃·(lnpop×educ) + β₄·male + β₅·marr")
form("       + β₆·exp + β₇·exp² + 健康虚拟变量 + 行业固定效应 + 职业固定效应 + ε")
para("与前面几个模型相比，这一模型的关键变化是加入了行业（hangye，20 类）与职业（zhiye，8 类）"
     "两套固定效应。若直接用 reg 加上全部虚拟变量，需要引入 20 + 7 = 27 个虚拟变量；"
     "reghdfe 通过“吸收”把这两套固定效应投影掉，只估计核心系数，在高维固定效应下更快、更稳定。"
     "式 4.37A 是未中心化的写法，式 4.37B 是先 center 再相乘的写法。")

caption("表 7：例 4.37A / 4.37B 的估计结果（被解释变量：lnwage，吸收行业与职业固定效应）")
rows7 = [
    ("lnpop", {0: ("0.0796***", "(0.0043)"), 1: ("−0.1462***", "(0.0141)"), 2: ("—", "")}),
    ("educ", {0: ("0.0398***", "(0.0015)"), 1: ("−0.0925***", "(0.0080)"), 2: ("—", "")}),
    ("lnpop×educ", {1: ("0.0201***", "(0.0012)"), 2: ("—", "")}),
    ("lnpop（中心化）", {2: ("0.0836***", "(0.0043)"), 0: ("—", ""), 1: ("—", "")}),
    ("educ（中心化）", {2: ("0.0401***", "(0.0015)"), 0: ("—", ""), 1: ("—", "")}),
    ("lnpop×educ（中心化）", {2: ("0.0201***", "(0.0012)"), 0: ("—", ""), 1: ("—", "")}),
    ("male", {0: ("0.1806***", "(0.0078)"), 1: ("0.1841***", "(0.0077)"),
              2: ("0.1841***", "(0.0077)")}),
    ("marr", {0: ("0.0748***", "(0.0099)"), 1: ("0.0722***", "(0.0098)"),
              2: ("0.0722***", "(0.0098)")}),
    ("exp", {0: ("0.0284***", "(0.0013)"), 1: ("0.0284***", "(0.0013)"),
             2: ("0.0284***", "(0.0013)")}),
    ("exp2", {0: ("−0.00068***", "(0.00003)"), 1: ("−0.00068***", "(0.00003)"),
              2: ("−0.00068***", "(0.00003)")}),
    ("health=2", {0: ("0.0920**", "(0.0420)"), 1: ("0.1217***", "(0.0416)"),
                  2: ("0.1217***", "(0.0416)")}),
    ("health=3", {0: ("0.1505***", "(0.0412)"), 1: ("0.1796***", "(0.0409)"),
                  2: ("0.1796***", "(0.0409)")}),
    ("_cons", {0: ("6.8020***", "(0.0527)"), 1: ("8.2486***", "(0.1004)"),
               2: ("7.7428***", "(0.0421)")}),
]
stats7 = [("N", ["14,757"] * 3), ("R²", ["0.2857", "0.2992", "0.2992"]),
          ("Within R²", ["0.1745", "0.1902", "0.1902"])]
three_line(esttab_like(
    ["(1) 无交互", "(2) 式4.37A", "(3) 式4.37B"],
    ["reghdfe"] * 3, rows7, stats7, size=8.5))
note("注：括号内为标准误；*、**、*** 分别表示 10%、5%、1% 显著。三列均吸收行业（20 类）"
     "与职业（8 类）固定效应，用 reghdfe 估计，MWFE 迭代 8 次收敛。"
     "health 的基准组为 health=1，未报告的 20 个行业系数与 7 个职业系数被吸收。")

h2("5.1 式 4.37A：reghdfe 与 margins")
para("表 7 第 (1) 列是不含交互项的对照模型：lnpop 0.0796（在 1% 水平显著），"
     "控制行业、职业固定效应后城市规模弹性仍有约 8%，说明城市规模溢价不是行业或职业构成差异造成的。"
     "第 (2) 列是式 4.37A：交互项 lnpop×educ 系数 0.0201（标准误 0.0012），t = 16.87，在 1% 水平显著；"
     "lnpop −0.1462、educ −0.0925 同样是外推值。"
     "R² 由 0.2857 升至 0.2992，Within R² 由 0.1745 升至 0.1902，交互项带来了实质性的解释力增量。"
     "其他控制变量的方向与实验一完全一致：male 0.1841（男性高约 "
     f"{pct(0.1841):.1f}%）、marr 0.0722（已婚高约 {pct(0.0722):.1f}%）、"
     "exp 0.0284 与 exp² −0.00068（倒 U 形），健康状况越好工资越高（health=3 相对 health=1 高约 "
     f"{pct(0.1796):.1f}%）。")
para("式 4.37A 在 Stata 中的实现是：", after=2)
form("reghdfe lnwage c.lnpop##c.educ male marr exp exp2 i.health, absorb(hangye zhiye)")
para("这条命令与 reg lnwage c.lnpop##c.educ male marr exp exp2 i.health i.hangye i.zhiye 的系数"
     "逐位相同（均为 lnpop −0.146212、educ −0.092538、交互项 0.020114），区别只在于后者会把 27 个"
     "虚拟变量系数全部打印出来、消耗自由度，前者只报告核心系数并额外输出“吸收的自由度数”。"
     "求偏效应用 margins，例如 margins, dydx(lnpop educ) atmeans 在样本均值（lnpop 6.596、educ 11.425）处"
     "给出 ∂lnwage/∂lnpop = 0.0836、∂lnwage/∂educ = 0.0401，即“平均劳动者的城市规模弹性约 8.4%、"
     "教育回报约 4.0%”。")
para("需要提醒的是，reghdfe 存估计后与 margins、_b[] 的配合有两点限制，实验中已实际遇到并绕过："
     "其一，因子变量 c.lnpop##c.educ 生成的交互项系数名含 #，reghdfe 的 e(b) 把名称拼接为 c.lnpop#c.educ，"
     "因此 _b[lnpop_x_educ] 与 _b[c.lnpop#c.educ] 都取不到，若要手工计算偏效应，"
     "应另用 gen lnpop_x_educ = lnpop*educ 手工生成乘积项再重新估计（两种写法的系数完全相同，"
     "lnpop −0.146212、educ −0.092538、交互项 0.020114 逐位一致）；"
     "其二，reghdfe 之后 margins 的 at() 设定对交互项不起作用（dydx(lnpop) at(educ=(6 9 ...)) 会给出常数），"
     "所以表 8 的偏效应一律按式 4.30 用系数手工计算。")

caption("表 8：式 4.37A 下的城市规模弹性（按式 4.30 手工计算）")
t8 = pd.DataFrame([
    ["6（小学）", "−0.0255", "−2.52"],
    ["9（初中）", "0.0348", "3.54"],
    ["12（高中）", "0.0952", "9.99"],
    ["15（大专）", "0.1555", "16.83"],
    ["16（本科）", "0.1756", "19.20"],
    ["19（研究生）", "0.2360", "26.62"],
], columns=["受教育年限", "∂lnwage/∂lnpop", "城市人口 +1% 时工资 +（%）"])
three_line(add_table(t8))
note("注：偏效应 = β₁ + β₃·educ = −0.14621 + 0.020114·educ，取式 4.37A（表 7 第 (2) 列）的系数。"
     "用 lincom lnpop + 16*lnpop_x_educ 可验证 educ = 16 年的弹性为 0.1756（标准误 0.0071）。")
para("表 8 与表 6 的结论一致且更可信：加入行业、职业固定效应与全部控制变量后，"
     "城市规模弹性仍随教育单调上升（小学 −2.5%，高中 10.0%，本科 19.2%，研究生 26.6%），"
     "系数从表 6 的 0.0221 微降到 0.0201，说明即便剔除行业、职业构成的差异，"
     "“城市规模工资溢价对高教育劳动者更大”这一结论依然稳健——这正是教材在 4.5 节末尾给出的结论。")

h2("5.2 式 4.37B：center 中心化")
para("式 4.37B 先用 Stata 的 center 命令生成中心化变量，再相乘：", after=2)
form("center lnpop educ")
form("reghdfe lnwage c.c_lnpop##c.c_educ male marr exp exp2 i.health, absorb(hangye zhiye)")
para("表 7 第 (3) 列显示：交互项系数仍为 0.0201（标准误 0.0012），与第 (2) 列逐位相同；"
     "R² 同为 0.2992、Within R² 同为 0.1902；male、marr、exp、exp² 与两个健康虚拟变量的系数也分毫未变。"
     "唯一变化的是 lnpop、educ 的系数：由 −0.1462、−0.0925 变为 0.0836、0.0401。"
     "这不是估计结果变了，而是坐标原点变了——中心化把“lnpop = 0、educ = 0 时的外推值”"
     "平移成“对方取均值时的偏效应”。按式 4.33 验证："
     "−0.14621 + 0.020114×11.42495 = 0.08359，−0.092538 + 0.020114×6.596233 = 0.04014，"
     "与第 (3) 列报告的 0.0836、0.0401 完全吻合。"
     "margins, dydx(c_lnpop c_educ) atmeans 亦直接给出 0.0836 与 0.0401（中心化变量的均值近似为 0）。")
para("因此式 4.37A 与 4.37B 是同一个模型的两种等价写法。实践中推荐式 4.37B："
     "中心化后的主效应本身就是有经济含义的偏效应（平均劳动者的城市规模弹性 8.4%、教育回报 4.0%），"
     "不需要再额外计算；而式 4.37A 的主效应是外推值，容易被误读为“大城市工资更低”。")

h2("5.3 稳健性：分组回归")
para("为确认结论不是交互项设定造成的，把样本按教育程度分成两组分别回归：educ ≤ 9（学历在初中及以下，"
     "N = 6,589）与 educ ≥ 15（学历在大专及以上，N = 4,546），两组都控制全部变量与两套固定效应。")
caption("表 9：按教育程度分组的稳健性检验")
t9 = pd.DataFrame([
    ["lnpop", "0.0372***", "(0.0058)", "0.1646***", "(0.0088)"],
    ["educ", "−0.0013", "(0.0034)", "0.1598***", "(0.0087)"],
    ["male", "0.2080***", "(0.0110)", "0.1519***", "(0.0150)"],
    ["marr", "0.0645***", "(0.0144)", "0.0400**", "(0.0188)"],
    ["exp", "0.0195***", "(0.0020)", "0.0492***", "(0.0034)"],
    ["exp2", "−0.00057***", "(0.00004)", "−0.00103***", "(0.00011)"],
    ["N", "6,589", "", "4,546", ""],
    ["R²", "0.2278", "", "0.3313", ""],
], columns=["变量", "初中及以下", "标准误", "大专及以上", "标准误"])
three_line(add_table(t9, size=8.5))
note("注：*、**、*** 分别表示 10%、5%、1% 显著。两组均控制 male、marr、exp、exp²、"
     "健康虚拟变量以及行业、职业固定效应；health 两个虚拟变量的系数未列出。")
para("分组回归给出了完全一致的结论：初中学历组的城市规模弹性仅 0.0372（标准误 0.0058），"
     "大专以上组高达 0.1646（标准误 0.0088），后者约为前者的 4.4 倍。"
     "值得注意的是初中学历组的 educ 系数 −0.0013 不显著（t = −0.39），"
     "说明在这一学历区间内，多读一两年书对工资几乎没有额外作用，教育回报主要集中在高中以上；"
     "而大专以上组的教育回报高达 0.1598（约每年 17.3%）。"
     "男性的系数在低学历组更高（0.2080 vs 0.1519）、婚姻溢价在低学历组也存在（0.0645），"
     "这些与实验一的结论方向一致。"
     "分组回归不依赖交互项的具体函数形式，因此可作为交互项模型结论的独立佐证。")

# ================================================================ 六、结论
def para_concl(text):
    """结论部分：略紧的行距与段距，使五条结论排在同一页内。"""
    _p = para(text, after=2)
    _p.paragraph_format.line_spacing = 1.30
    return _p


h1("六、结论")
para_concl("本实验用 wage_chap4.dta（N = 14,757）完成教材第 11 页与第 17 页全部内容，主要结论如下。")
para_concl("第一，函数形式的选择直接决定系数的含义，不能只看 R²。"
     "水平—水平模型的系数是绝对变化量（每多一年教育 292.53 元），半对数模型是百分比变化"
     "（每年教育约 5.25%），线性—对数模型是“X 变动 1% 时 Y 的绝对变化”（人口多 1% 工资高 7.05 元），"
     "双对数模型是弹性（城市规模弹性 0.114，与教材式 4.14 精确吻合）。"
     "经验对工资呈倒 U 形，须引入 exp²，转折点 16.35 年；"
     "去掉平方项 exp 系数反号为 −0.0069，F（760.31）与 nestreg 增量 R²（0.0479）均显示平方项必要。")
para_concl("第二，交互项的设定必须与偏效应的解读配套。"
     "式 4.23 中 male×educ 系数 0.0102 显著，性别工资差异随教育递增：未上学者 21.5%、"
     "高中 27.1%、本科 29.0%、研究生 30.5%；男性教育回报 6.23%、女性 5.15%。"
     "式 4.29 中定量×定量的交互更要注意：交互项显著后未中心化的主效应（−0.1661、−0.0982）"
     "只是外推值，须按式 4.30 逐点算偏效应——城市规模弹性从小学的 −0.034 升到 0.253。")
para_concl("第三，中心化是解读交互项模型的标准做法。把 educ 减去均值 11.4250 后，"
     "式 4.23 的 male 系数从 0.1946 变为 0.2375，恰为教育均值处的性别差异；"
     "把 lnpop 与 educ 同时中心化后，式 4.29 的主效应变成 0.0859 与 0.0473，"
     "即偏效应在对方均值处的取值。"
     "交互项系数（0.0102、0.0221、0.0201）与 R² 在中心化前后完全不变，"
     "可见中心化只是平移坐标原点，属解释技巧而非模型改动。")
para_concl("第四，reghdfe 可吸收高维固定效应，且与 reg 加全部虚拟变量等价。"
     "式 4.37A 吸收行业（20 类）与职业（8 类）固定效应后，交互项 0.0201，"
     "R² 由 0.2857 升至 0.2992；"
     "式 4.37B 用 center 中心化后重估，交互项与所有控制变量系数逐位不变，主效应变为均值处的偏效应"
     "（0.0836、0.0401）。实测中因子交互项系数名含 #，_b[] 取不到，须手工生成乘积项；"
     "reghdfe 之后的 margins at() 对交互项也须手工计算。")
para_concl("第五，核心经济结论稳健。式 4.29（弹性 −0.034~0.253）、式 4.37A（−0.026~0.236）"
     "与按教育分组回归（0.0372 vs 0.1646）三条证据都指向同一命题："
     "城市规模工资溢价随教育水平提高而增大，高学历者是大城市集聚效应的主要受益者，"
     "与教材 4.5 节结论一致。")

# ================================================================ 附录：代码
doc.add_page_break()
h1("附录：运行代码")
para("实验二共两个 do 文件，均放在「实验二」文件夹内，用相对路径读取「演示数据\\wage_chap4.dta」。"
     "运行方式（批处理）：", after=2)
form('"D:\\Stata\\StataMP-64.exe" -e do 01_p11函数形式.do')
form('"D:\\Stata\\StataMP-64.exe" -e do 02_p17交互项.do')
para("02_p17交互项.do 需要 ftools、reghdfe、center 三个第三方命令。本机向 C:\\Users\\omori\\ado\\plus 写入被拒绝，"
     "因此已把它们及依赖（require、moremata）下载到工作区的 ado_work 目录，并在 do 文件开头用 "
     'adopath ++ "..\\ado_work" 挂载；若本机已能 ssc install ftools reghdfe center，'
     "可删去该行。star 系列的显著性标注与结果核对另由 Python 复算校验。", after=4)


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
        set_cn(q.add_run(line if line.strip() else " "), "Consolas", 7.5, ea="宋体")


for _f in ["01_p11函数形式.do", "02_p17交互项.do"]:
    _p = os.path.join(EXP2, _f)
    if os.path.exists(_p):
        code_block(open(_p, encoding="utf-8").read(), f"Stata do 文件（{_f}）")

# 去掉文末多余的空段落，避免多出一张空白页
while doc.paragraphs and not doc.paragraphs[-1].text.strip():
    _el = doc.paragraphs[-1]._element
    if _el.find(qn("w:r")) is not None or _el.find(qn("w:pPr")) is not None:
        pass
    _el.getparent().remove(_el)

doc.save(DOCX)
print("已保存:", DOCX)
