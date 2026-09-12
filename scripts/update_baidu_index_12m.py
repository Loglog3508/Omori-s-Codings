# -*- coding: utf-8 -*-
"""Write the verified Baidu Index 12-month weekly-proxy trend into the workbook."""

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = next(
    p
    for p in ROOT.rglob("*.xlsx")
    if p.name == "大学生哑铃_市场分析数据与计算.xlsx"
)


ROWS = [
    # month, current displayed weekly point, year-ago matching weekly point,
    # current week period, year-ago week period
    ("2025-09", 500, 693, "2025-09-08 ~ 2025-09-14", "2024-09-09 ~ 2024-09-15"),
    ("2025-10", 517, 692, "2025-10-13 ~ 2025-10-19", "2024-10-07 ~ 2024-10-13"),
    ("2025-11", 466, 690, "2025-11-10 ~ 2025-11-16", "2024-11-04 ~ 2024-11-10"),
    ("2025-12", 427, 598, "2025-12-08 ~ 2025-12-14", "2024-12-02 ~ 2024-12-08"),
    ("2026-01", 373, 595, "2026-01-05 ~ 2026-01-11", "2024-12-30 ~ 2025-01-05"),
    ("2026-02", 350, 454, "2026-02-02 ~ 2026-02-08", "2025-01-27 ~ 2025-02-02"),
    ("2026-03", 398, 629, "2026-03-02 ~ 2026-03-08", "2025-02-17 ~ 2025-02-23"),
    ("2026-04", 485, 722, "2026-03-30 ~ 2026-04-05", "2025-04-14 ~ 2025-04-20"),
    ("2026-05", 390, 621, "2026-04-27 ~ 2026-05-03", "2025-05-12 ~ 2025-05-18"),
    ("2026-06", 389, 648, "2026-05-25 ~ 2026-05-31", "2025-06-09 ~ 2025-06-15"),
    ("2026-07", 424, 577, "2026-07-20 ~ 2026-07-26", "2025-07-07 ~ 2025-07-13"),
    ("2026-08", 365, 519, "2026-08-17 ~ 2026-08-23", "2025-08-04 ~ 2025-08-10"),
]


def main() -> None:
    wb = load_workbook(WORKBOOK, data_only=False)
    ws = wb["百度指数录入"]

    ws["A1"] = "百度指数：哑铃 - 12个月可见周值趋势代理与增长判断"
    ws["A2"] = "月份（趋势代理）"
    ws["B2"] = "本期可见周值"
    ws["C2"] = "去年同期可见周值"
    ws["D2"] = "同比增速"
    ws["E2"] = "上期可见周值"
    ws["F2"] = "环比增速"
    ws["G2"] = "数据来源"
    ws["H2"] = "可复核周区间与口径"

    input_fill = PatternFill("solid", fgColor="FFF2CC")
    input_font = Font(name="Arial", color="0000FF")
    source_text = (
        "百度指数，关键词“哑铃”，全国、PC+移动；"
        "查询日2026-09-10，图表区间2024-09-01 ~ 2026-08-31"
    )
    note = (
        "图表在该长区间按周显示；本表按每月一条可见周值记录，"
        "用于趋势和同比方向判断，不是百度官方“月均指数”。"
    )

    for row_number, (month, current, prior_year, current_period, prior_period) in enumerate(
        ROWS, start=3
    ):
        ws.cell(row_number, 1).value = month
        ws.cell(row_number, 2).value = current
        ws.cell(row_number, 3).value = prior_year
        ws.cell(row_number, 4).value = (
            f'=IF(OR(B{row_number}="",C{row_number}=""),"",B{row_number}/C{row_number}-1)'
        )
        ws.cell(row_number, 5).value = None if row_number == 3 else f"=B{row_number - 1}"
        ws.cell(row_number, 6).value = (
            f'=IF(OR(B{row_number}="",E{row_number}=""),"",B{row_number}/E{row_number}-1)'
        )
        ws.cell(row_number, 7).value = source_text
        ws.cell(row_number, 8).value = (
            f"本期：{current_period}（{current}）；去年同期：{prior_period}（{prior_year}）。{note}"
        )
        for column in (2, 3):
            cell = ws.cell(row_number, column)
            cell.fill = input_fill
            cell.font = input_font
            cell.number_format = "#,##0"
            cell.comment = Comment(
                f"来自登录后的百度指数可见图表提示。本期：{current_period}={current}；"
                f"去年同期：{prior_period}={prior_year}。{note}",
                "Codex",
            )
        ws.cell(row_number, 4).number_format = "0.0%"
        ws.cell(row_number, 6).number_format = "0.0%"
        for column in range(1, 9):
            ws.cell(row_number, column).alignment = Alignment(
                vertical="top", wrap_text=True
            )

    ws["A16"] = "行业生命周期判定规则（按课堂图示）"
    ws["B16"] = (
        "增长率 < -10%：衰退期；-10% 至 10%：成熟期；增长率 > 10%：成长期。"
        "本表12条均为可见周值趋势代理，须结合供给、竞争和季节性判断。"
    )
    ws.merge_cells("B16:H16")

    ws["A21"] = "2024-09-01 ~ 2026-08-31（自定义）"
    ws["B21"] = 521
    ws["C21"] = 416
    ws["F21"] = source_text
    ws["G21"] = (
        "两年区间整体日均值；本表上方12条为周粒度趋势代理，"
        "可用于观察连续同比下行，不能表述为月均指数。"
    )

    ws.column_dimensions["A"].width = 17
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 43
    ws.column_dimensions["H"].width = 62
    ws.freeze_panes = "A3"

    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.save(WORKBOOK)


if __name__ == "__main__":
    main()
