# -*- coding: utf-8 -*-
"""
生成《时间序列分析》第三章作业 Word 报告。
运行：D:\\Python\\python.exe 生成报告.py
输出：大数据2班洪翼雄2407150229.docx
"""

import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "图")
OUT = os.path.join(BASE, "大数据2班洪翼雄2407150229.docx")

FONT_CN = "宋体"
FONT_HEI = "黑体"
FONT_EN = "Times New Roman"
FONT_CODE = "Consolas"

doc = Document()

# ----------------------------------------------------------------------
# 页面设置
# ----------------------------------------------------------------------
sec = doc.sections[0]
sec.page_width = Cm(21)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.4)
sec.bottom_margin = Cm(2.4)
sec.left_margin = Cm(2.8)
sec.right_margin = Cm(2.6)
sec.different_first_page_header_footer = True

# ----------------------------------------------------------------------
# 样式基础
# ----------------------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = FONT_EN
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)


def set_run_font(run, font_cn=FONT_CN, font_en=FONT_EN, size=None,
                 bold=None, italic=None, color=None):
    run.font.name = font_en
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font_cn)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


import re

TOKEN_RE = re.compile(r"(_\{[^}]*\}|\^\{[^}]*\})")


def add_rich_text(p, text, size=10.5, font_cn=FONT_CN, font_en=FONT_EN,
                  bold=False, italic=False):
    """把含 _{下标} / ^{上标} 标记的文字写入段落。"""
    for part in TOKEN_RE.split(text):
        if not part:
            continue
        sub = sup = False
        if part.startswith("_{") and part.endswith("}"):
            content, sub = part[2:-1], True
        elif part.startswith("^{") and part.endswith("}"):
            content, sup = part[2:-1], True
        else:
            content = part
        run = p.add_run(content)
        set_run_font(run, font_cn, font_en, size, bold, italic)
        if sub:
            run.font.subscript = True
        if sup:
            run.font.superscript = True


def add_heading_cn(text, level=1):
    style = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3"}[level]
    p = doc.add_paragraph(style=style)
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    if level == 1:
        fmt.space_before = Pt(16)
        fmt.space_after = Pt(8)
        size = 16
    elif level == 2:
        fmt.space_before = Pt(10)
        fmt.space_after = Pt(5)
        size = 13
    else:
        fmt.space_before = Pt(8)
        fmt.space_after = Pt(4)
        size = 11.5
    fmt.keep_with_next = True
    add_rich_text(p, text, size=size, font_cn=FONT_HEI, font_en=FONT_EN, bold=True)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
    return p


def add_body(text, size=10.5, indent=True, align=None, space_before=0,
             space_after=0, bold=False):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    if indent:
        fmt.first_line_indent = Pt(size * 2)
    if align is not None:
        p.alignment = align
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    add_rich_text(p, text, size=size, bold=bold)
    return p


def add_formula(text, size=11):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    fmt.space_before = Pt(3)
    fmt.space_after = Pt(3)
    add_rich_text(p, text, size=size, font_en="Cambria Math")
    return p


def shade_paragraph(p, fill):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def border_paragraph(p, color="BFBFBF", sz=4, edges=("top", "left", "bottom", "right")):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "4")
        el.set(qn("w:color"), color)
        pBdr.append(el)
    pPr.append(pBdr)


def add_code(text):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    fmt.left_indent = Cm(0.4)
    fmt.right_indent = Cm(0.2)
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(4)
    fmt.line_spacing = 1.0
    fmt.keep_together = True
    shade_paragraph(p, "F5F5F5")
    border_paragraph(p)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i:
            p.add_run().add_break()
        run = p.add_run(line if line else " ")
        set_run_font(run, font_cn=FONT_CODE, font_en=FONT_CODE, size=8.5)
    return p


def add_caption(text, keep_next=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    fmt.space_before = Pt(2)
    fmt.space_after = Pt(6)
    fmt.keep_with_next = keep_next
    add_rich_text(p, text, size=9, bold=True)
    return p


def add_figure(filename, caption, width_cm=15.2):
    path = os.path.join(FIG, filename)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    fmt.space_before = Pt(6)
    fmt.space_after = Pt(2)
    fmt.keep_with_next = True
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    add_caption(caption)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_cell(cell, text, size=8.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    fmt = p.paragraph_format
    fmt.line_spacing = 1.15
    fmt.space_before = Pt(1)
    fmt.space_after = Pt(1)
    add_rich_text(p, text, size=size, bold=bold)


def mark_row(row, repeat_header=False):
    """设置表格行属性：不跨页断开；表头行跨页重复。"""
    trPr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    cant.set(qn("w:val"), "true")
    trPr.append(cant)
    if repeat_header:
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        trPr.append(hdr)


def add_table(headers, rows, widths_cm, caption=None, header_fill="DCE6F1"):
    if caption:
        add_caption(caption, keep_next=True)
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    mark_row(table.rows[0], repeat_header=True)
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        set_cell(hdr[i], h, size=8.5, bold=True)
        shade_cell(hdr[i], header_fill)
        hdr[i].width = Cm(widths_cm[i])
    for row in rows:
        tr = table.add_row()
        mark_row(tr)
        cells = tr.cells
        for i, val in enumerate(row):
            set_cell(cells[i], val, size=8.5)
            cells[i].width = Cm(widths_cm[i])
    # 让整张表尽量保持在同一页：除最后一行外，各行段落都“与下段同页”
    for tr in table.rows[:-1]:
        for cell in tr.cells:
            for pp in cell.paragraphs:
                pp.paragraph_format.keep_with_next = True
    return table


def add_page_break():
    doc.add_page_break()


# ----------------------------------------------------------------------
# 页眉页脚
# ----------------------------------------------------------------------
header = sec.header
hp = header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hr = hp.add_run("时间序列分析  第三章作业　大数据2班  洪翼雄  2407150229")
set_run_font(hr, size=8, color=(0x80, 0x80, 0x80))
border_paragraph(hp, color="A6A6A6", sz=6, edges=("bottom",))

footer = sec.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = fp.add_run("第 ")
set_run_font(r1, size=9)
run = fp.add_run()
set_run_font(run, size=9)
fld1 = OxmlElement("w:fldChar")
fld1.set(qn("w:fldCharType"), "begin")
instr = OxmlElement("w:instrText")
instr.set(qn("xml:space"), "preserve")
instr.text = "PAGE"
fld2 = OxmlElement("w:fldChar")
fld2.set(qn("w:fldCharType"), "end")
run._r.append(fld1)
run._r.append(instr)
run._r.append(fld2)
r3 = fp.add_run(" 页")
set_run_font(r3, size=9)

# ----------------------------------------------------------------------
# 文档属性
# ----------------------------------------------------------------------
doc.core_properties.title = "时间序列分析 第三章 平稳时间序列模型（ARMA模型）习题与代码"
doc.core_properties.author = "洪翼雄"
doc.core_properties.subject = "时间序列分析课程作业"

# ======================================================================
# 封面
# ======================================================================
for _ in range(3):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_rich_text(p, "时间序列分析", size=30, font_cn=FONT_HEI, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
add_rich_text(p, "第三章  平稳时间序列模型（ARMA 模型）", size=20, font_cn=FONT_HEI, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(4)
add_rich_text(p, "课 后 习 题 与 代 码", size=18, font_cn=FONT_HEI, bold=True)

# 分隔线
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(10)
pPr = p._p.get_or_add_pPr()
pBdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "12")
bottom.set(qn("w:space"), "1")
bottom.set(qn("w:color"), "000000")
pBdr.append(bottom)
pPr.append(pBdr)

for _ in range(4):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)

info = [("班　　级", "大数据2班"),
        ("姓　　名", "洪翼雄"),
        ("学　　号", "2407150229"),
        ("课程名称", "时间序列分析"),
        ("提交日期", "2026 年 11 月 20 日")]
from docx.enum.text import WD_TAB_ALIGNMENT

for label, value in info:
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.first_line_indent = None
    fmt.left_indent = Cm(3.9)
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(4)
    fmt.tab_stops.add_tab_stop(Cm(8.2), WD_TAB_ALIGNMENT.RIGHT)
    fmt.tab_stops.add_tab_stop(Cm(8.5), WD_TAB_ALIGNMENT.LEFT)
    add_rich_text(p, label + "：\t" + value, size=14, font_cn=FONT_CN)

add_page_break()

# ======================================================================
# 作业说明
# ======================================================================
add_heading_cn("作业说明", 1)
add_body(
    "本次作业围绕第三章“平稳时间序列模型”展开，对应老师下发的资料"
    "《11.20 第三章习题及代码》，共包含四个部分："
)
for item in [
    "（1）计算题：随机游走一阶差分序列的平稳性与自相关系数；第 11 题 6 个 ARMA 模型的平稳性、可逆性检验。",
    "（2）AR 模型：用 for 循环生成四个 AR 模型序列，绘制 ACF 图与 PACF 图，观察拖尾、截尾特征。",
    "（3）MA 模型：自行编写代码生成四个 MA 模型序列，绘制 ACF 图与 PACF 图，观察拖尾、截尾特征。",
    "（4）课后习题 16、17：对澳大利亚枪支凶杀案死亡率序列和密歇根湖年度最高水位序列作时序图与 ACF/PACF 分析。",
]:
    add_body(item, indent=True)

add_body(
    "所有计算题均给出完整的推导过程；所有代码均在本机实际运行通过，"
    "运行结果（图片与数值）直接粘贴在报告中。程序文件共五个，"
    "分别对应上述四个部分，统一放在“课程作业2”文件夹下，运行说明见附录。"
)

# ======================================================================
# 一、计算题
# ======================================================================
add_heading_cn("一、计算题", 1)

add_heading_cn("（一）第（2）题：一阶差分序列的平稳性与自相关系数", 2)
add_body(
    "题目：设 {x_{t}} 为随机游走序列 x_{t} = x_{t−1} + ε_{t}，其中 {ε_{t}} 为白噪声序列，"
    "E(ε_{t}) = 0，Var(ε_{t}) = σ^{2}，令 y_{t} = x_{t} − x_{t−1}。"
    "证明 {x_{t}} 的一阶差分序列 {y_{t}} 一定是平稳序列，并求 {y_{t}} 的自相关系数。"
)
add_body("解：由一阶差分的定义，有", indent=True)
add_formula("y_{t} = x_{t} − x_{t−1} = ε_{t}")
add_body(
    "即一阶差分序列 {y_{t}} 恰好是原模型的扰动项 {ε_{t}}，也就是白噪声序列。下面验证平稳性的三个条件："
)
add_body("（1）均值为常数：E(y_{t}) = E(ε_{t}) = 0；")
add_body("（2）方差为常数：Var(y_{t}) = Var(ε_{t}) = σ^{2}；")
add_body("（3）自协方差只与时间间隔 k 有关：")
add_formula("γ_{k} = Cov(y_{t}, y_{t−k}) = Cov(ε_{t}, ε_{t−k})")
add_formula("即　γ_{0} = Var(y_{t}) = σ^{2}（k = 0）；　γ_{k} = 0（k ≠ 0）")
add_body(
    "可见均值、方差均为常数，自协方差只依赖于间隔 k，因此 {y_{t}} 是平稳序列。"
    "进一步，其自相关系数为"
)
add_formula("ρ_{0} = 1；　ρ_{k} = γ_{k} / γ_{0} = 0　（k = 1, 2, 3, …）")
add_body(
    "即 {y_{t}} 的自相关图在 0 阶以后全部为 0，呈现“0 阶截尾”的特征，"
    "自相关系数表如下："
)
add_table(
    ["k", "0", "1", "2", "3", "4", "5", "6", "…"],
    [["ρ_{k}", "1", "0", "0", "0", "0", "0", "0", "…"]],
    [2.0, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
    caption="表 1-1　随机游走一阶差分序列的自相关系数表",
)
add_body(
    "补充说明：若随机游走带有漂移项，即 x_{t} = x_{t−1} + μ + ε_{t}，则 "
    "y_{t} = μ + ε_{t}，仍然是平稳序列（均值 μ、方差 σ^{2} 均为常数），"
    "自协方差与自相关系数的结论不变，仍有 ρ_{0} = 1、ρ_{k} = 0（k ≥ 1）。"
)
add_body(
    "从差分算子的角度看，随机游走是 1 阶单整序列 I(1)，经过一次差分（1 − B）"
    "后化为 0 阶单整的平稳序列 I(0)，这正是 ARIMA 模型中“差分使序列平稳”的基本思想。"
)

add_heading_cn("（二）第 11 题：检验模型的平稳性与可逆性", 2)
add_body(
    "题目：检验下列模型的平稳性与可逆性，其中 {ε_{t}} 为白噪声序列："
)
add_formula("（1）x_{t} = 0.5x_{t−1} + 1.2x_{t−2} + ε_{t}　　（2）x_{t} = 1.1x_{t−1} − 0.3x_{t−2} + ε_{t}")
add_formula("（3）x_{t} = ε_{t} − 0.9ε_{t−1} + 0.3ε_{t−2}　　（4）x_{t} = ε_{t} + 1.3ε_{t−1} − 0.4ε_{t−2}")
add_formula("（5）x_{t} = 0.7x_{t−1} + ε_{t} − 0.6ε_{t−1}　　（6）x_{t} = −0.8x_{t−1} + 0.5x_{t−2} + ε_{t} − 1.1ε_{t−1}")

add_heading_cn("1. 判别准则", 3)
add_body(
    "一般的 ARMA(p, q) 模型可写成 Φ(B)x_{t} = Θ(B)ε_{t}，其中"
)
add_formula("Φ(z) = 1 − φ_{1}z − φ_{2}z^{2} − … − φ_{p}z^{p}")
add_formula("Θ(z) = 1 + θ_{1}z + θ_{2}z^{2} + … + θ_{q}z^{q}")
add_body(
    "（1）平稳性：AR 模型的特征多项式 Φ(z) 的根全部位于单位圆外时，模型平稳。"
    "若用特征根 λ（满足 λ^{p} − φ_{1}λ^{p−1} − … − φ_{p} = 0）表示，则平稳性条件为所有 |λ| < 1。"
)
add_body(
    "（2）可逆性：MA 模型的特征多项式 Θ(z) 的根全部位于单位圆外时，模型可逆，即所有 |z| > 1。"
    "对 ARMA(p, q) 模型，平稳要求 AR 部分平稳，可逆要求 MA 部分可逆。"
)
add_body(
    "（3）低阶模型的常用判别域：AR(2) 平稳域为 |φ_{2}| < 1、φ_{1} + φ_{2} < 1、φ_{2} − φ_{1} < 1；"
    "MA(2) 可逆域为 |θ_{2}| < 1、θ_{1} + θ_{2} > −1、θ_{2} − θ_{1} > −1。"
    "另外，有限阶 MA 模型本身一定是平稳的，纯 AR 模型本身一定是可逆的。"
)

add_heading_cn("2. 逐题求解", 3)

add_body("（1）x_{t} = 0.5x_{t−1} + 1.2x_{t−2} + ε_{t}，这是 AR(2) 模型，φ_{1} = 0.5，φ_{2} = 1.2。")
add_body("特征方程为", indent=True)
add_formula("λ^{2} − 0.5λ − 1.2 = 0")
add_body("解得 λ_{1} = 1.3736，λ_{2} = −0.8736。由于 |λ_{1}| = 1.3736 > 1，特征根没有全部落在单位圆内，")
add_body(
    "故该模型非平稳。也可用 AR(2) 平稳域判断：φ_{1} + φ_{2} = 0.5 + 1.2 = 1.7 > 1，"
    "不满足平稳条件。模型不含 MA 部分，可逆性自然成立。"
)
add_body("结论：非平稳。")

add_body("（2）x_{t} = 1.1x_{t−1} − 0.3x_{t−2} + ε_{t}，AR(2) 模型，φ_{1} = 1.1，φ_{2} = −0.3。")
add_body("特征方程为", indent=True)
add_formula("λ^{2} − 1.1λ + 0.3 = 0")
add_body(
    "解得 λ_{1} = 0.6，λ_{2} = 0.5，两个特征根的模都小于 1。"
    "用平稳域检验：|φ_{2}| = 0.3 < 1，φ_{1} + φ_{2} = 0.8 < 1，φ_{2} − φ_{1} = −1.4 < 1，同样满足平稳条件。"
)
add_body("结论：平稳且（无 MA 部分时）可逆。")

add_body(
    "（3）x_{t} = ε_{t} − 0.9ε_{t−1} + 0.3ε_{t−2}，MA(2) 模型，θ_{1} = −0.9，θ_{2} = 0.3。"
    "MA 模型是有限阶移动平均，一定是平稳的，只需检验可逆性。"
)
add_body("令 Θ(z) = 1 − 0.9z + 0.3z^{2} = 0，解得", indent=True)
add_formula("z = 1.5 ± 1.0408i，　|z| = √(1.5^{2} + 1.0408^{2}) = 1.8257 > 1")
add_body(
    "特征根全部在单位圆外，故模型可逆。也可用 MA(2) 可逆域检验：|θ_{2}| = 0.3 < 1，"
    "θ_{1} + θ_{2} = −0.6 > −1，θ_{2} − θ_{1} = 1.2 > −1，满足可逆条件。"
)
add_body("结论：平稳且可逆。")

add_body(
    "（4）x_{t} = ε_{t} + 1.3ε_{t−1} − 0.4ε_{t−2}，MA(2) 模型，θ_{1} = 1.3，θ_{2} = −0.4，"
    "模型平稳，只需检验可逆性。"
)
add_body("令 Θ(z) = 1 + 1.3z − 0.4z^{2} = 0，即 0.4z^{2} − 1.3z − 1 = 0，解得", indent=True)
add_formula("z_{1} = 3.8923，　z_{2} = −0.6423")
add_body(
    "由于 |z_{2}| = 0.6423 < 1，有一个特征根落在单位圆内，因此模型不可逆。"
    "用可逆域检验：θ_{2} − θ_{1} = −0.4 − 1.3 = −1.7 < −1，不满足可逆条件，与特征根结果一致。"
)
add_body("结论：平稳但不可逆。")

add_body("（5）x_{t} = 0.7x_{t−1} + ε_{t} − 0.6ε_{t−1}，这是 ARMA(1, 1) 模型，φ_{1} = 0.7，θ_{1} = −0.6。")
add_body(
    "平稳性：|φ_{1}| = 0.7 < 1，AR 部分平稳；可逆性：令 1 − 0.6z = 0，得 z = 1.6667，|z| > 1，MA 部分可逆。"
)
add_body("结论：平稳且可逆。")

add_body(
    "（6）x_{t} = −0.8x_{t−1} + 0.5x_{t−2} + ε_{t} − 1.1ε_{t−1}，ARMA(2, 1) 模型，"
    "φ_{1} = −0.8，φ_{2} = 0.5，θ_{1} = −1.1。"
)
add_body("AR 部分特征方程：λ^{2} + 0.8λ − 0.5 = 0，解得", indent=True)
add_formula("λ_{1} = 0.4124，　λ_{2} = −1.2124")
add_body(
    "由于 |λ_{2}| = 1.2124 > 1，AR 部分不平稳，整个模型非平稳"
    "（平稳域检验：φ_{2} − φ_{1} = 0.5 − (−0.8) = 1.3 > 1，不满足）。"
)
add_body("MA 部分：令 1 − 1.1z = 0，得 z = 0.9091，|z| < 1，MA 部分也不可逆。")
add_body("结论：非平稳（且不可逆）。")

add_heading_cn("3. 小结", 3)
add_body("六个模型的判别结果汇总于表 1-2。")
add_table(
    ["题号", "模型类型", "特征根与判别", "平稳性", "可逆性"],
    [
        ["（1）", "AR(2)", "λ_{1}=1.3736，λ_{2}=−0.8736，|λ_{1}|>1", "非平稳", "—"],
        ["（2）", "AR(2)", "λ_{1}=0.6，λ_{2}=0.5，均满足|λ|<1", "平稳", "—"],
        ["（3）", "MA(2)", "z=1.5±1.0408i，|z|=1.8257>1", "平稳", "可逆"],
        ["（4）", "MA(2)", "z_{1}=3.8923，z_{2}=−0.6423，|z_{2}|<1", "平稳", "不可逆"],
        ["（5）", "ARMA(1,1)", "AR：λ=0.7；MA：z=1.6667", "平稳", "可逆"],
        ["（6）", "ARMA(2,1)", "AR：λ_{2}=−1.2124，|λ_{2}|>1；MA：z=0.9091", "非平稳", "不可逆"],
    ],
    [1.4, 2.2, 7.6, 1.8, 1.8],
    caption="表 1-2　第 11 题各模型的平稳性与可逆性判别结果",
)
add_body(
    "由表 1-2 可见：模型（2）、（3）、（5）的平稳条件全部满足，其中（2）是纯 AR 模型，"
    "不含 MA 部分，可逆性自然成立；（3）、（5）同时还满足可逆性，是比较理想的 ARMA 模型；"
    "（1）、（6）的 AR 部分含有模大于 1 的特征根，是非平稳模型；（4）虽然是平稳的，但 MA 特征根落在单位圆内，不可逆。"
    "上述手算结果已用程序（1_计算题.py，numpy.roots 求根）逐题核对，数值完全一致。"
)

# ======================================================================
# 二、AR 模型
# ======================================================================
add_heading_cn("二、AR 模型的 ACF 图与 PACF 图", 1)

add_heading_cn("（一）题目", 2)
add_body(
    "运行下面四个 AR 模型的 ACF 图和 PACF 图，观察其拖尾、截尾特征（用 for 循环生成序列）。"
)
for txt in [
    "（1）x_{t} = 0.8x_{t−1} + ε_{t}",
    "（2）x_{t} = −0.8x_{t−1} + ε_{t}",
    "（3）x_{t} = x_{t−1} − 0.5x_{t−2} + ε_{t}",
    "（4）x_{t} = −x_{t−1} − 0.5x_{t−2} + ε_{t}",
]:
    add_formula(txt, size=10.5)
add_body(
    "其中 {ε_{t}} 为白噪声，样本量取 n = 100，与老师给出的代码保持一致。"
)

add_heading_cn("（二）代码实现", 2)
add_code(r"""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

np.random.seed(20261120)          # 固定随机种子，保证结果可复现
N = 100
X = np.zeros((N, 4))
e = np.random.normal(size=N)

for i in range(N - 1):            # 前两个 AR(1)
    X[i + 1, 0] = 0.8 * X[i, 0] + e[i]
    X[i + 1, 1] = -0.8 * X[i, 1] + e[i]
for i in range(N - 2):            # 后两个 AR(2)
    X[i + 2, 2] = X[i + 1, 2] - 0.5 * X[i, 2] + e[i]
    X[i + 2, 3] = -X[i + 1, 3] - 0.5 * X[i, 3] + e[i]

df = pd.DataFrame(X, columns=['X1', 'X2', 'X3', 'X4'])
titles = {'X1': 'X1: φ1 = 0.8', 'X2': 'X2: φ1 = -0.8',
          'X3': 'X3: φ1 = 1, φ2 = -0.5', 'X4': 'X4: φ1 = -1, φ2 = -0.5'}
CI = 2 / np.sqrt(N)               # ±2/√n 近似 95% 置信界限

# 四个模型的时序图
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.4))
for ax, col in zip(axes.flat, df.columns):
    ax.plot(np.arange(1, N + 1), df[col], linewidth=0.9)
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.set_title(titles[col])
    ax.set_xlabel('t'); ax.set_ylabel('x'); ax.grid(alpha=0.3)
fig.suptitle('四个 AR 模型的时序图（n = 100）', fontsize=13)
fig.tight_layout()
fig.savefig('图/AR四模型_时序图.png', dpi=200)""")
add_body("接着分别绘制四个模型的 ACF 图与 PACF 图：")
add_code(r"""fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, df.columns):
    plot_acf(df[col], lags=20, ax=ax, title=titles[col], alpha=None)
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
fig.suptitle('四个 AR 模型的样本自相关图（ACF）', fontsize=13)
fig.tight_layout()
fig.savefig('图/AR四模型_ACF图.png', dpi=200)

fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, df.columns):
    plot_pacf(df[col], lags=20, ax=ax, method='ywm', title=titles[col], alpha=None)
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
fig.suptitle('四个 AR 模型的样本偏自相关图（PACF）', fontsize=13)
fig.tight_layout()
fig.savefig('图/AR四模型_PACF图.png', dpi=200)
plt.show()""")
add_body(
    "说明：完整脚本见“课程作业2/2_AR模型.py”（其中还包含时序图的绘制与前 6 阶相关系数的输出）。"
)

add_heading_cn("（三）运行结果", 2)
add_figure("AR四模型_时序图.png", "图 2-1　四个 AR 模型的时序图（n = 100）", width_cm=13.4)
add_figure("AR四模型_ACF图.png", "图 2-2　四个 AR 模型的样本自相关图（ACF）", width_cm=13.4)
add_figure("AR四模型_PACF图.png", "图 2-3　四个 AR 模型的样本偏自相关图（PACF）", width_cm=13.4)
add_body(
    "说明：图 2-2、图 2-3 中红色虚线为 ±2/√n = ±0.200 的近似 95% 置信界限，"
    "相关系数超出该界限即可认为显著不为 0。"
)

add_body("各模型前 6 阶样本自相关系数见表 2-1，前 6 阶样本偏自相关系数见表 2-2。")
add_table(
    ["模型", "k=1", "k=2", "k=3", "k=4", "k=5", "k=6"],
    [
        ["X1", "0.670", "0.375", "0.190", "0.046", "−0.064", "−0.031"],
        ["X2", "−0.789", "0.625", "−0.562", "0.499", "−0.493", "0.427"],
        ["X3", "0.630", "0.069", "−0.322", "−0.464", "−0.410", "−0.189"],
        ["X4", "−0.613", "0.078", "0.178", "−0.136", "−0.028", "0.030"],
    ],
    [2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    caption="表 2-1　四个 AR 模型的样本自相关系数（前 6 阶）",
)
add_table(
    ["模型", "k=1", "k=2", "k=3", "k=4", "k=5", "k=6"],
    [
        ["X1", "0.670", "−0.133", "−0.011", "−0.081", "−0.070", "0.136"],
        ["X2", "−0.789", "0.007", "−0.177", "0.007", "−0.176", "−0.125"],
        ["X3", "0.630", "−0.545", "−0.109", "−0.169", "−0.138", "0.040"],
        ["X4", "−0.613", "−0.476", "−0.088", "0.046", "−0.064", "−0.194"],
    ],
    [2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    caption="表 2-2　四个 AR 模型的样本偏自相关系数（前 6 阶）",
)
add_body(
    "说明：n = 100 时，样本自相关系数的 2 倍标准误约为 2/√n = 0.200，"
    "可以据此粗略判断某阶相关系数是否显著异于 0。"
)

add_heading_cn("（四）结果分析", 2)
add_body(
    "（1）X1：x_{t} = 0.8x_{t−1} + ε_{t}。由表 2-1，ACF 从 0.670 开始依次为 0.375、0.190、0.046、…，"
    "呈指数式衰减且始终为正，表现为“拖尾”；由表 2-2，PACF 在 k = 1 处为 0.670，k = 2 以后"
    "（−0.133、−0.011、−0.081、…）都落在 ±0.2 的随机区间内，表现为“1 阶截尾”。"
    "这正是 AR(1) 模型的典型特征，理论自相关系数 ρ_{k} = 0.8^{k}（0.800、0.640、0.512、…）"
    "也与样本值的变化趋势一致。"
)
add_body(
    "（2）X2：x_{t} = −0.8x_{t−1} + ε_{t}。ACF 为 −0.789、0.625、−0.562、0.499、…，"
    "符号正负交替、绝对值逐渐减小，同样表现为“拖尾”；PACF 在 1 阶以后同样迅速落入随机区间，"
    "表现为“1 阶截尾”。这是系数为负的 AR(1) 模型的特征，理论 ACF 为 ρ_{k} = (−0.8)^{k}。"
)
add_body(
    "（3）X3：x_{t} = x_{t−1} − 0.5x_{t−2} + ε_{t}。ACF 依次为 0.630、0.069、−0.322、−0.464、…，"
    "围绕 0 上下振荡并逐渐衰减，表现为“拖尾”；PACF 在 k = 1、2 处分别为 0.630、−0.545，"
    "数值较大，k = 3 以后（−0.109、−0.169、−0.138、…）都落入随机区间，表现为“2 阶截尾”。"
    "因此 X3 是 AR(2) 模型。"
)
add_body(
    "（4）X4：x_{t} = −x_{t−1} − 0.5x_{t−2} + ε_{t}。ACF 为 −0.613、0.078、0.178、−0.136、…，"
    "呈振荡衰减的“拖尾”形态；PACF 在 k = 1、2 处为 −0.613、−0.476，k ≥ 3 后落入随机区间，"
    "呈“2 阶截尾”。因此 X4 也是 AR(2) 模型。"
)
add_body(
    "小结：四个 AR 模型的 ACF 都是拖尾的，PACF 分别在 1 阶或 2 阶截尾，"
    "与“AR(p) 模型自相关系数拖尾、偏自相关系数 p 阶截尾”的识别规律完全一致。"
)
add_table(
    ["模型", "ACF", "PACF", "识别结果"],
    [
        ["X1", "指数衰减（拖尾）", "1 阶截尾", "AR(1)，φ_{1}=0.8"],
        ["X2", "正负交替衰减（拖尾）", "1 阶截尾", "AR(1)，φ_{1}=−0.8"],
        ["X3", "振荡衰减（拖尾）", "2 阶截尾", "AR(2)"],
        ["X4", "振荡衰减（拖尾）", "2 阶截尾", "AR(2)"],
    ],
    [2.0, 5.0, 3.0, 5.0],
    caption="表 2-3　四个 AR 模型的拖尾、截尾特征与识别结果",
)

# ======================================================================
# 三、MA 模型
# ======================================================================
add_heading_cn("三、MA 模型的 ACF 图与 PACF 图", 1)

add_heading_cn("（一）题目", 2)
add_body(
    "运行下面四个 MA 模型的 ACF 图和 PACF 图，观察其拖尾、截尾特征（自行编写代码）。"
)
for txt in [
    "（1）x_{t} = ε_{t} − 2ε_{t−1}",
    "（2）x_{t} = ε_{t} − 0.5ε_{t−1}",
    "（3）x_{t} = ε_{t} − (4/5)ε_{t−1} + (16/25)ε_{t−2}",
    "（4）x_{t} = ε_{t} − (5/4)ε_{t−1} + (25/16)ε_{t−2}",
]:
    add_formula(txt, size=10.5)

add_heading_cn("（二）代码实现", 2)
add_code(r"""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

np.random.seed(2024)
N = 100
E = np.random.normal(size=N + 2)          # 多生成两项供 MA(2) 使用

theta = [(-2.0, 0.0), (-0.5, 0.0), (-0.8, 0.64), (-1.25, 1.5625)]
X = np.zeros((N, 4))
for j, (t1, t2) in enumerate(theta):
    for t in range(N):
        # E[k] 代表 ε_(k−2)，故 E[t+2]=ε_t，E[t+1]=ε_(t−1)，E[t]=ε_(t−2)
        X[t, j] = E[t + 2] + t1 * E[t + 1] + t2 * E[t]

df = pd.DataFrame(X, columns=['X1', 'X2', 'X3', 'X4'])
titles = {'X1': 'X1: θ1 = -2', 'X2': 'X2: θ1 = -0.5',
          'X3': 'X3: θ1 = -0.8, θ2 = 0.64', 'X4': 'X4: θ1 = -1.25, θ2 = 1.5625'}
CI = 2 / np.sqrt(N)               # ±2/√n 近似 95% 置信界限""")
add_body("然后绘制四个模型的时序图，再分别绘制 ACF 图与 PACF 图：")
add_code(r"""# 四个模型的时序图
fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.4))
for ax, col in zip(axes.flat, df.columns):
    ax.plot(np.arange(1, N + 1), df[col], linewidth=0.9)
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.set_title(titles[col])
    ax.set_xlabel('t'); ax.set_ylabel('x'); ax.grid(alpha=0.3)
fig.suptitle('四个 MA 模型的时序图（n = 100）', fontsize=13)
fig.tight_layout()
fig.savefig('图/MA四模型_时序图.png', dpi=200)""")
add_body("接着分别绘制四个模型的 ACF 图与 PACF 图：")
add_code(r"""fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, df.columns):
    plot_acf(df[col], lags=20, ax=ax, title=titles[col], alpha=None)
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
fig.suptitle('四个 MA 模型的样本自相关图（ACF）', fontsize=13)
fig.tight_layout()
fig.savefig('图/MA四模型_ACF图.png', dpi=200)

fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.7))
for ax, col in zip(axes.flat, df.columns):
    plot_pacf(df[col], lags=20, ax=ax, method='ywm', title=titles[col], alpha=None)
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
fig.suptitle('四个 MA 模型的样本偏自相关图（PACF）', fontsize=13)
fig.tight_layout()
fig.savefig('图/MA四模型_PACF图.png', dpi=200)
plt.show()""")
add_body("说明：完整脚本见“课程作业2/3_MA模型.py”。")

add_heading_cn("（三）运行结果", 2)
add_figure("MA四模型_时序图.png", "图 3-1　四个 MA 模型的时序图（n = 100）", width_cm=13.4)
add_figure("MA四模型_ACF图.png", "图 3-2　四个 MA 模型的样本自相关图（ACF）", width_cm=13.4)
add_figure("MA四模型_PACF图.png", "图 3-3　四个 MA 模型的样本偏自相关图（PACF）", width_cm=13.4)
add_body(
    "说明：图 3-2、图 3-3 中的红色虚线同样为 ±2/√n = ±0.200 的近似 95% 置信界限。"
)

add_body("各模型前 6 阶样本自相关系数见表 3-1，前 6 阶样本偏自相关系数见表 3-2。")
add_table(
    ["模型", "k=1", "k=2", "k=3", "k=4", "k=5", "k=6"],
    [
        ["X1", "−0.409", "−0.111", "0.019", "0.123", "−0.085", "−0.023"],
        ["X2", "−0.409", "−0.111", "0.015", "0.118", "−0.075", "−0.017"],
        ["X3", "−0.655", "0.247", "−0.020", "0.072", "−0.078", "−0.053"],
        ["X4", "−0.649", "0.245", "−0.020", "0.074", "−0.073", "−0.062"],
    ],
    [2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    caption="表 3-1　四个 MA 模型的样本自相关系数（前 6 阶）",
)
add_table(
    ["模型", "k=1", "k=2", "k=3", "k=4", "k=5", "k=6"],
    [
        ["X1", "−0.409", "−0.334", "−0.240", "−0.021", "−0.050", "−0.053"],
        ["X2", "−0.409", "−0.334", "−0.246", "−0.036", "−0.053", "−0.045"],
        ["X3", "−0.655", "−0.321", "−0.032", "0.233", "0.184", "−0.161"],
        ["X4", "−0.649", "−0.304", "−0.021", "0.233", "0.187", "−0.159"],
    ],
    [2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
    caption="表 3-2　四个 MA 模型的样本偏自相关系数（前 6 阶）",
)

add_heading_cn("（四）结果分析", 2)
add_body(
    "（1）X1：x_{t} = ε_{t} − 2ε_{t−1}。ACF 在 k = 1 处为 −0.409，k = 2 以后（−0.111、0.019、…）"
    "基本落入随机区间，表现为“1 阶截尾”；PACF 依次为 −0.409、−0.334、−0.240、…，缓慢衰减，表现为“拖尾”。"
    "因此 X1 是 MA(1) 模型，θ_{1} = −2。理论值 ρ_{1} = θ_{1}/(1 + θ_{1}^{2}) = −2/5 = −0.4，与样本值接近。"
)
add_body(
    "（2）X2：x_{t} = ε_{t} − 0.5ε_{t−1}。ACF 同样在 1 阶截尾（k = 1 为 −0.409，k ≥ 2 近似为 0），"
    "PACF 拖尾，因此也是 MA(1) 模型，θ_{1} = −0.5。理论值 ρ_{1} = −0.5/1.25 = −0.4，与 X1 相同。"
)
add_body(
    "（3）X3：x_{t} = ε_{t} − 0.8ε_{t−1} + 0.64ε_{t−2}。ACF 在 k = 1、2 处为 −0.655、0.247，"
    "k = 3 以后（−0.020、0.072、…）基本为 0，表现为“2 阶截尾”；PACF 在 1~2 阶以后仍缓慢波动（0.233、0.184、−0.161、…），"
    "表现为“拖尾”。因此 X3 是 MA(2) 模型，θ_{1} = −0.8，θ_{2} = 0.64。"
    "理论值 ρ_{1} = θ_{1}(1 + θ_{2})/(1 + θ_{1}^{2} + θ_{2}^{2}) = −0.640，ρ_{2} = θ_{2}/(1 + θ_{1}^{2} + θ_{2}^{2}) = 0.312。"
)
add_body(
    "（4）X4：x_{t} = ε_{t} − 1.25ε_{t−1} + 1.5625ε_{t−2}。ACF 与 X3 几乎完全相同（−0.649、0.245，k = 3 以后为 0），"
    "PACF 同样拖尾，因此也是 MA(2) 模型，θ_{1} = −1.25，θ_{2} = 1.5625。"
)
add_body(
    "值得注意：X1 与 X2 的 ACF 几乎一样（1 阶截尾，ρ_{1} ≈ −0.4），X3 与 X4 的 ACF 也几乎一样"
    "（2 阶截尾，ρ_{1} ≈ −0.64、ρ_{2} ≈ 0.31），但它们的参数并不相同。原因是对 MA 模型而言，"
    "只要 θ 与 1/θ 互换，自相关系数就相同，因此仅凭 ACF 无法唯一确定 MA 模型。"
    "这时要靠可逆性条件来取舍：X1 的 θ_{1} = −2（|θ_{1}| > 1）不可逆，X4 的 Θ(z) 根落在单位圆内也不可逆，"
    "只有可逆的 X2（θ_{1} = −0.5）与 X3（θ_{1} = −0.8、θ_{2} = 0.64）才对应唯一的平稳可逆表示。"
)
add_body(
    "小结：四个 MA 模型的 PACF 都拖尾，ACF 分别在 1 阶或 2 阶截尾，"
    "与“MA(q) 模型自相关系数 q 阶截尾、偏自相关系数拖尾”的识别规律一致。"
)
add_table(
    ["模型", "ACF", "PACF", "识别结果"],
    [
        ["X1", "1 阶截尾", "缓慢衰减（拖尾）", "MA(1)，θ_{1}=−2（不可逆）"],
        ["X2", "1 阶截尾", "缓慢衰减（拖尾）", "MA(1)，θ_{1}=−0.5（可逆）"],
        ["X3", "2 阶截尾", "振荡衰减（拖尾）", "MA(2)，θ=(−0.8, 0.64)（可逆）"],
        ["X4", "2 阶截尾", "振荡衰减（拖尾）", "MA(2)，θ=(−1.25, 1.5625)（不可逆）"],
    ],
    [1.6, 3.2, 3.6, 6.6],
    caption="表 3-3　四个 MA 模型的拖尾、截尾特征与识别结果",
)

# ======================================================================
# 四、习题 16
# ======================================================================
add_heading_cn("四、课后习题 16：澳大利亚枪支凶杀案死亡率", 1)

add_heading_cn("（一）题目与数据", 2)
add_body(
    "题目：1915—2004 年澳大利亚每年与枪支有关的凶杀案死亡率（每 10 万人）如表 3-5 所示。"
    "（1）绘制该序列的时序图，直观考察该序列的平稳特征；"
    "（2）判断该序列的自相关系数与偏自相关系数的截尾或拖尾特征。"
)
add_body(
    "数据文件为 E2_7.xlsx（year、mortality 两列，共 90 个观测），"
    "样本均值 0.4840，标准差 0.1519，最小值 0.1589（2004 年），最大值 0.8280（1919 年）。"
    "为便于按时间顺序分析，将年份设置为年度周期索引后再绘图。"
)

add_heading_cn("（二）代码实现", 2)
add_code(r"""import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

df = pd.read_excel('../课程资料1/习题数据/E2_7.xlsx')
df.index = pd.PeriodIndex(df['year'], freq='Y')
x, n = df['mortality'], len(df)
CI = 2 / np.sqrt(n)                       # ±2/√n ≈ ±0.211

# (1) 时序图
fig, ax = plt.subplots(figsize=(8.0, 3.0))
ax.plot(df.index.astype(str), x.values, linewidth=1.2)
ax.set_xticks([str(y) for y in df['year'].values[::10]])
ax.set_xlabel('年份')
ax.set_ylabel('死亡率（每 10 万人）')
ax.set_title('1915—2004 年澳大利亚枪支凶杀案死亡率时序图')
ax.grid(alpha=0.3)""")
add_body("接着绘制自相关图与偏自相关图：")
add_code(r"""# (2) 自相关图与偏自相关图
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1))
plot_acf(x, lags=24, ax=axes[0], title='mortality 的自相关图（ACF）', alpha=None)
plot_pacf(x, lags=24, ax=axes[1], method='ywm', title='mortality 的偏自相关图（PACF）',
          alpha=None)
for ax in axes:
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
plt.show()""")
add_body("说明：完整脚本见“课程作业2/4_习题16.py”，图片保存于“图”目录。")

add_heading_cn("（三）时序图与平稳性直观判断", 2)
add_figure("习题16_时序图.png", "图 4-1　1915—2004 年澳大利亚枪支凶杀案死亡率时序图")
add_body(
    "从图 4-1 可以看出：该序列没有围绕一个固定的水平上下波动。1915—1985 年间死亡率在较高水平上反复震荡"
    "（大致在 0.24~0.83 之间），其中 1919 年出现 0.828 的峰值；而 1985 年以后序列持续下降，"
    "由 1985 年的约 0.60 一路降到 2004 年的 0.159。均值水平随时间发生明显改变，"
    "因此从时序图可以直观判断该序列是非平稳序列（存在长期下降趋势）。"
)

add_heading_cn("（四）ACF 与 PACF 的截尾、拖尾判断", 2)
add_figure("习题16_ACF与PACF图.png", "图 4-2　死亡率的自相关图（左）与偏自相关图（右）")
add_body(
    "图 4-2 中红色虚线为 ±2/√n = ±0.211 的近似 95% 置信界限（n = 90）。"
)
add_body(
    "自相关图（图 4-2 左）显示，样本自相关系数从 r_{1} = 0.561 开始缓慢衰减："
    "0.462、0.376、0.400、0.324、0.210、…，前 9 阶均为正，衰减速度明显慢于平稳序列；"
    "到 13 阶以后才转为负值，24 阶时仍有 −0.229。这种“缓慢衰减、长期为正”的形态是"
    "带趋势的非平稳序列的典型自相关特征，属于拖尾。"
)
add_body(
    "偏自相关图（图 4-2 右）显示，只有 1 阶偏自相关系数 0.561 明显异于 0，"
    "2 阶以后（0.215、0.080、0.173、…）基本都落在 ±2/√n = ±0.211 的随机区间内，"
    "呈现出明显的 1 阶截尾特征。"
)
add_body(
    "综合判断：该序列的 ACF 拖尾、PACF 1 阶截尾，具有 AR(1) 模型的特征；"
    "但时序图和 ACF 又表明序列本身是非平稳的，所以在建模时通常需要先对序列作适当的"
    "差分或趋势处理，再按 AR(1) 模型进行拟合。"
)

add_heading_cn("（五）结论", 2)
add_body(
    "（1）时序图：序列均值随时间改变、1985 年后持续下降，可判定为非平稳序列。"
    "（2）相关图：自相关系数缓慢衰减、呈拖尾；偏自相关系数 1 阶截尾，"
    "说明该序列具有 AR(1) 模型的特征。"
)

# ======================================================================
# 五、习题 17
# ======================================================================
add_heading_cn("五、课后习题 17：密歇根湖年度最高水位", 1)

add_heading_cn("（一）题目与数据", 2)
add_body(
    "题目：1860—1955 年密歇根湖每月平均水位的最高值序列如表 3-6 所示。"
    "（1）绘制该序列的时序图，直观考察该序列的平稳特征；"
    "（2）根据样本自相关图和偏自相关图，判断该序列的自相关系数与偏自相关系数的截尾或拖尾特征。"
)
add_body(
    "数据文件为 E2_8.xlsx（year、wl 两列，共 96 个观测），"
    "样本均值 81.1766，标准差 1.3224，最小值 78.0（1934 年），最大值 83.7（1886 年）。"
)

add_heading_cn("（二）代码实现", 2)
add_code(r"""import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

df = pd.read_excel('../课程资料1/习题数据/E2_8.xlsx')
df.index = pd.PeriodIndex(df['year'], freq='Y')
x, n = df['wl'], len(df)
CI = 2 / np.sqrt(n)                       # ±2/√n ≈ ±0.204

# (1) 时序图
fig, ax = plt.subplots(figsize=(8.0, 3.0))
ax.plot(df.index.astype(str), x.values, linewidth=1.2)
ax.set_xticks([str(y) for y in df['year'].values[::10]])
ax.set_xlabel('年份')
ax.set_ylabel('水位（英尺）')
ax.set_title('1860—1955 年密歇根湖年度最高水位时序图')
ax.grid(alpha=0.3)""")
add_body("接着绘制自相关图与偏自相关图：")
add_code(r"""# (2) 自相关图与偏自相关图
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1))
plot_acf(x, lags=24, ax=axes[0], title='wl 的自相关图（ACF）', alpha=None)
plot_pacf(x, lags=24, ax=axes[1], method='ywm', title='wl 的偏自相关图（PACF）',
          alpha=None)
for ax in axes:
    ax.axhline(CI, color='red', linestyle='--', linewidth=0.8)
    ax.axhline(-CI, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('延迟 k')
    ax.grid(alpha=0.3)
plt.show()""")
add_body("说明：完整脚本见“课程作业2/5_习题17.py”，图片保存于“图”目录。")

add_heading_cn("（三）时序图与平稳性直观判断", 2)
add_figure("习题17_时序图.png", "图 5-1　1860—1955 年密歇根湖年度最高水位时序图")
add_body(
    "从图 5-1 可以看出：水位序列呈明显的长周期起伏。1860—1886 年在 81.6~83.7 的高位波动，"
    "1887—1935 年回落到 78.0~82.3 的低位，1936—1955 年又回升到 78.6~82.7。"
    "整个样本期内水位在 78~83.7 之间大范围涨落，均值水平并非常数，"
    "序列没有表现出围绕固定均值波动的特征，因此可直观判断为非平稳序列"
    "（其涨落周期与样本长度相当，呈现长记忆、慢衰减的特点）。"
)

add_heading_cn("（四）ACF 与 PACF 的截尾、拖尾判断", 2)
add_figure("习题17_ACF与PACF图.png", "图 5-2　水位的自相关图（左）与偏自相关图（右）")
add_body(
    "图 5-2 中红色虚线为 ±2/√n = ±0.204 的近似 95% 置信界限（n = 96）。"
)
add_body(
    "自相关图（图 5-2 左）显示，样本自相关系数从 r_{1} = 0.850 开始非常缓慢地衰减："
    "0.667、0.552、0.499、0.469、0.446、…，一直到 24 阶仍有 0.165，"
    "几乎呈线性缓慢下降并长期保持为正，属于典型的拖尾形态。这种衰减速度远慢于"
    "平稳序列应有的速度，进一步说明序列非平稳。"
)
add_body(
    "偏自相关图（图 5-2 右）显示，1 阶偏自相关系数为 0.850，明显异于 0；"
    "2 阶以后（−0.203、0.161、0.095、…）基本都落在 ±2/√n = ±0.204 的随机区间内，"
    "呈现 1 阶截尾特征。"
)
add_body(
    "综合判断：该序列的 ACF 拖尾、PACF 1 阶截尾，具有 AR(1) 模型的特征；"
    "同时时序图与 ACF 的缓慢衰减表明序列非平稳，建模前应先作差分或趋势处理。"
)

add_heading_cn("（五）结论", 2)
add_body(
    "（1）时序图：水位在 1860—1955 年间呈长周期涨落，均值随时间改变，可判定为非平稳序列。"
    "（2）相关图：自相关系数衰减极慢、呈拖尾；偏自相关系数 1 阶截尾，"
    "说明该序列具有 AR(1) 模型的特征。"
)

# ======================================================================
# 六、小结
# ======================================================================
add_heading_cn("六、小结", 1)

add_heading_cn("（一）AR、MA、ARMA 模型的识别规律", 2)
add_body(
    "通过本次作业中四个 AR 模型、四个 MA 模型的模拟与相关图分析，可以总结出如下识别规律："
)
add_table(
    ["模型", "自相关函数 ACF", "偏自相关函数 PACF"],
    [
        ["AR(p)", "拖尾（指数或振荡衰减）", "p 阶截尾"],
        ["MA(q)", "q 阶截尾", "拖尾（指数或振荡衰减）"],
        ["ARMA(p, q)", "拖尾", "拖尾"],
    ],
    [3.6, 6.4, 6.0],
    caption="表 6-1　AR、MA、ARMA 模型的 ACF、PACF 识别规律",
)
add_body(
    "需要注意：截尾、拖尾的判断带有一定的主观性，应结合 2/√n 的置信区间以及模型的"
    "定阶准则（如 AIC、BIC）综合确定阶数。"
)

add_heading_cn("（二）平稳性与可逆性的判别要点", 2)
add_body(
    "（1）平稳性只由 AR 部分决定：AR 特征多项式 Φ(z) 的根全部在单位圆外时模型平稳；"
    "等价地，特征根 λ 的模全部小于 1。"
)
add_body(
    "（2）可逆性只由 MA 部分决定：MA 特征多项式 Θ(z) 的根全部在单位圆外时模型可逆。"
)
add_body(
    "（3）MA 模型的自相关函数对参数不唯一：θ 与 1/θ 对应相同的 ACF，"
    "这正是要用可逆性条件确定唯一 MA 表示的原因。"
)

add_heading_cn("（三）差分的作用", 2)
add_body(
    "随机游走是 I(1) 序列，一阶差分后 y_{t} = x_{t} − x_{t−1} = ε_{t} 变成平稳的白噪声序列，"
    "自相关系数在 0 阶以后全为 0。这说明差分是消除趋势、使序列平稳的常用手段，"
    "也解释了 ARIMA(p, d, q) 模型中差分阶数 d 的含义。"
)
add_body(
    "本次作业把课本上的平稳性、可逆性判别条件用程序逐一验证，"
    "并通过 AR、MA 模型的模拟直观看到了“拖尾、截尾”的形态，"
    "加深了对 ARMA 模型识别方法的理解。"
)

# ======================================================================
# 附录
# ======================================================================
add_page_break()
add_heading_cn("附录　程序文件与运行说明", 1)
add_body("本次作业的全部程序文件均放在“课程作业2”文件夹下，清单如下：")
add_table(
    ["序号", "文件名", "对应内容"],
    [
        ["1", "1_计算题.py", "第 11 题 6 个模型特征根求根、平稳性与可逆性程序核对；随机游走差分验证"],
        ["2", "2_AR模型.py", "四个 AR 模型的时序图、ACF 图、PACF 图"],
        ["3", "3_MA模型.py", "四个 MA 模型的时序图、ACF 图、PACF 图"],
        ["4", "4_习题16.py", "习题 16 的时序图、ACF 图与 PACF 图"],
        ["5", "5_习题17.py", "习题 17 的时序图、ACF 图与 PACF 图"],
    ],
    [1.3, 4.2, 10.3],
    caption="表 A-1　程序文件清单",
)
add_body(
    "运行环境：Python 3.14，依赖 numpy、pandas、matplotlib、statsmodels、openpyxl。"
)
add_body(
    "运行方法：在“课程作业2”目录下执行 python 文件名.py，程序会自动在“图”子目录中"
    "生成对应的 png 图片；设置环境变量 HW_SHOW=1 可在运行时弹出图片窗口。"
)
add_body(
    "数据文件：课程资料1/习题数据/E2_7.xlsx、E2_8.xlsx（习题 16、17）；"
    "AR、MA 模型数据由程序按题目给定模型模拟生成（随机种子已在代码中固定，结果可复现）。"
)

doc.save(OUT)
print("已生成：", OUT)
