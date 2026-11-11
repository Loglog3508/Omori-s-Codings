# -*- coding: utf-8 -*-
"""
把 实验五/实验六 的 markdown 报告拼进 Word 模板（实验报告五六），排版对齐 报告三四。

用法:
  python build_reports.py <模板docx> <实验五md> <实验六md> <输出docx> <实验五图目录> <实验六图目录>

规格来源（实测 报告三四）:
  A4 21x29.7cm，页边距 L/R 1.50、T 1.00、B 2.00，页眉 1.50、页脚 1.75
  任务标题: 加粗 14pt 黑体, 段前 9pt 段后 4pt, 行距 1.6667
  正文:     10.5pt 宋体, 段后 3pt, 行距 1.3333, 首句加粗引导 + 正常文字
  插图:     居中, 宽 13.72cm, 段前 4pt 段后 2pt
  图注:     居中, 加粗 9.5pt 楷体, 段前 2pt 段后 5pt, 形如「图 5-1  说明」
  None-sz 处按 docDefaults sz=21（10.5pt）渲染
"""
import sys
import os
import re

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.stdout.reconfigure(encoding="utf-8")

BODY_PT = 10.5
SONG = "\u5b8b\u4f53"      # 宋体
HEI = "\u9ed1\u4f53"       # 黑体
KAI = "\u6977\u4f53"       # 楷体
FIG = "\u56fe"             # 图
COLON = "\uff1a"           # ：
IMAGE_W = Cm(13.72)


# ---------- 低层工具 ----------
def set_run_font(run, name, size=None, bold=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    rf.set(qn("w:eastAsia"), name)
    rf.set(qn("w:ascii"), name)
    rf.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold


def add_md_runs(par, text, base_font=SONG, base_size=BODY_PT):
    """把 **加粗** 与 `代码` 解析成 run"""
    text = text.replace("`", "")
    for seg in re.split(r"(\*\*.+?\*\*)", text):
        if not seg:
            continue
        bold = seg.startswith("**") and seg.endswith("**") and len(seg) > 4
        run = par.add_run(seg[2:-2] if bold else seg)
        set_run_font(run, base_font, base_size, bold)


def fmt_par(par, align=None, before=None, after=None, line=None, left=None):
    pf = par.paragraph_format
    if align is not None:
        par.alignment = align
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)
    if line is not None:
        pf.line_spacing = line
    if left is not None:
        pf.left_indent = Cm(left)


def new_par(doc):
    p = doc.add_paragraph()
    return p


def move_after(anchor_el, new_el, doc_part):
    anchor_el.addnext(new_el)


# ---------- 表格 ----------
def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "808080")
        borders.append(el)
    tbl_pr.append(borders)


def add_table(doc, rows, anchor, doc_part):
    ncol = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncol)
    table.autofit = True
    try:
        table.style = "Table Grid"
    except Exception:
        set_table_borders(table)
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = table.cell(i, j)
            cell.text = ""
            par = cell.paragraphs[0]
            txt = row[j] if j < len(row) else ""
            add_md_runs(par, txt, base_font=SONG, base_size=9)
            fmt_par(par, align=WD_ALIGN_PARAGRAPH.LEFT, before=1, after=1)
            for r in par.runs:
                r.font.bold = True if i == 0 else r.font.bold
    # 表后留白
    return table


# ---------- 解析 md ----------
def parse_md(path):
    """返回 [(kind, payload)]，kind: h2/h3/quote/par/num/img/table/list"""
    blocks = []
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("# ") and not s.startswith("## "):
            i += 1
            continue
        if s.startswith("## "):
            blocks.append(("h2", s[3:].strip()))
            i += 1
            continue
        if s.startswith("### "):
            blocks.append(("h3", s[4:].strip()))
            i += 1
            continue
        if s.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(("quote", " ".join(quote)))
            continue
        m = re.match(r"!\[(.*?)\]\((.*?)\)", s)
        if m:
            blocks.append(("img", (m.group(1), m.group(2))))
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw = lines[i].strip().strip("|")
                if re.match(r"^[\s:|-]+$", raw):
                    i += 1
                    continue
                rows.append([c.strip() for c in raw.split("|")])
                i += 1
            if rows:
                blocks.append(("table", rows))
            continue
        if s.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            blocks.append(("list", items))
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            blocks.append(("num", s))
            i += 1
            continue
        # 普通段落：合并到下一个空行
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#|!\[|\||- |\d+\.\s|>)", lines[i].strip()
        ):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("par", " ".join(para)))
    return blocks


# ---------- 渲染 ----------
def render_lab(doc, blocks, img_dir, lab_no, anchor, page_break_first=False):
    """把 blocks 依次插到 anchor 之后，返回新的 anchor 元素"""
    fig_no = 0
    cur_task = None
    for kind, payload in blocks:
        if kind == "h2":
            if payload.startswith("\u9644"):
                break   # 「附：复现说明」不进 Word 正文
            # 任务标题：中文序号 + 任务名（编号）
            p = new_par(doc)
            add_md_runs(p, payload, base_font=HEI, base_size=14)
            for r in p.runs:
                r.font.bold = True
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=9, after=4, line=1.6667)
            anchor.addnext(p._p)
            anchor = p._p
            cur_task = payload
        elif kind == "h3":
            p = new_par(doc)
            add_md_runs(p, payload, base_font=HEI, base_size=11)
            for r in p.runs:
                r.font.bold = True
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=6, after=2, line=1.3)
            anchor.addnext(p._p)
            anchor = p._p
        elif kind == "quote":
            p = new_par(doc)
            add_md_runs(p, payload, base_font=KAI, base_size=BODY_PT)
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=6, line=1.3333, left=0.4)
            anchor.addnext(p._p)
            anchor = p._p
        elif kind == "par":
            p = new_par(doc)
            add_md_runs(p, payload, base_font=SONG, base_size=BODY_PT)
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=3, line=1.3333)
            anchor.addnext(p._p)
            anchor = p._p
        elif kind == "num":
            p = new_par(doc)
            add_md_runs(p, payload, base_font=SONG, base_size=BODY_PT)
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=3, line=1.3333)
            anchor.addnext(p._p)
            anchor = p._p
        elif kind == "list":
            for it in payload:
                p = new_par(doc)
                run = p.add_run("\u00b7 ")   # ·
                set_run_font(run, SONG, BODY_PT, False)
                add_md_runs(p, it, base_font=SONG, base_size=BODY_PT)
                fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=2, line=1.3, left=0.4)
                anchor.addnext(p._p)
                anchor = p._p
        elif kind == "img":
            alt, rel = payload
            img_path = os.path.join(img_dir, os.path.basename(rel))
            if not os.path.exists(img_path):
                print("  !! missing image:", img_path)
                continue
            p = new_par(doc)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(img_path, width=IMAGE_W)
            fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=2)
            anchor.addnext(p._p)
            anchor = p._p
            fig_no += 1
            cap = new_par(doc)
            cr = cap.add_run("%s %d-%d  %s" % (FIG, lab_no, fig_no, alt))
            set_run_font(cr, KAI, 9.5, True)
            fmt_par(cap, align=WD_ALIGN_PARAGRAPH.CENTER, before=2, after=5)
            anchor.addnext(cap._p)
            anchor = cap._p
        elif kind == "table":
            table = add_table(doc, payload, anchor, doc)
            anchor.addnext(table._tbl)
            anchor = table._tbl
            # 表后补一个空段，避免与后续文字贴死
            p = new_par(doc)
            fmt_par(p, before=0, after=2)
            anchor.addnext(p._p)
            anchor = p._p
    return anchor


def fill_class_line(par, cls, name, sid):
    """把「班级：\t姓名：\t学号：」替换成已填内容，保留制表符"""
    text = "%s%s\t%s%s\t%s%s" % (
        "\u73ed\u7ea7" + COLON, cls,
        "\u59d3\u540d" + COLON, name,
        "\u5b66\u53f7" + COLON, sid,
    )
    for r in list(par.runs):
        r._element.getparent().remove(r._element)
    run = par.add_run(text)
    set_run_font(run, SONG, 14, False)


def main():
    tpl_path, md5, md6, out_path, img5, img6 = sys.argv[1:7]
    doc = Document(tpl_path)
    body = doc.element.body
    print("template paras:", len(doc.paragraphs),
          "| page breaks:", doc.element.xml.count('w:type="page"'))

    # 定位两个实验标题与班级行
    h5 = h6 = None
    for p in doc.paragraphs:
        t = p.text.strip()
        if "\u5b9e\u9a8c5" in t:
            h5 = p
        elif "\u5b9e\u9a8c6" in t:
            h6 = p
    assert h5 is not None and h6 is not None, "找不到实验5/实验6 标题"
    cls5 = h5._p.getnext()
    cls6 = h6._p.getnext()
    for el, hdr in ((cls5, "5"), (cls6, "6")):
        from docx.text.paragraph import Paragraph
        fill_class_line(Paragraph(el, doc), "\u5927\u6570\u636e242", "\u6d2a\u7ffc\u96c4", "242-29")
    print("class lines filled")

    # 分页：只有前面没有现成分页符时才补 page_break_before，避免多出空白页
    def has_page_break_ahead(par_el, span=4):
        el = par_el.getprevious()
        for _ in range(span):
            if el is None:
                return False
            if el.tag.endswith("}p") and 'w:type="page"' in el.xml:
                return True
            el = el.getprevious()
        return False

    if not has_page_break_ahead(h5._p):
        h5.paragraph_format.page_break_before = True
    if not has_page_break_ahead(h6._p):
        h6.paragraph_format.page_break_before = True

    # 实验五内容：插到 h5 的班级行之后
    blocks5 = parse_md(md5)
    print("lab5 blocks:", len(blocks5))
    anchor = cls5
    render_lab(doc, blocks5, img5, 5, anchor)

    # 实验六内容：插到 h6 的班级行之后（先保证分页）
    if md6 and os.path.exists(md6):
        blocks6 = parse_md(md6)
        print("lab6 blocks:", len(blocks6))
        anchor6 = cls6
        render_lab(doc, blocks6, img6, 6, anchor6)

    doc.save(out_path)
    print("saved:", out_path)


if __name__ == "__main__":
    main()
