"""报告生成与可视化辅助模块。"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd


def generate_analysis_report(sections: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """整合多个分析输出并为每条记录标注所属模块。"""
    formatted: List[pd.DataFrame] = []
    for title, data in sections.items():
        if data is None:
            continue
        section_df = data.copy()
        if not isinstance(section_df, pd.DataFrame):
            section_df = pd.DataFrame(section_df)
        section_df = section_df.reset_index(drop=True)
        section_df.insert(0, "Section", title)
        formatted.append(section_df)
    return pd.concat(formatted, ignore_index=True, sort=False) if formatted else pd.DataFrame()


def save_report(report: pd.DataFrame, output_path: Path) -> None:
    """将分析报告保存为 CSV 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False, encoding="utf-8-sig")


def initialize_plot_style() -> str | None:
    """配置支持中文的字体，返回所用字体名称。"""
    candidates = ["SimHei", "Microsoft YaHei", "Microsoft YaHei UI", "DengXian", "STSong"]
    for font_name in candidates:
        try:
            font_path = font_manager.findfont(font_name, fallback_to_default=False)
        except ValueError:
            continue
        if font_path:
            plt.rcParams["font.sans-serif"] = [font_name]
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return font_name
    plt.rcParams["axes.unicode_minus"] = False
    return None


def render_visual_dashboard(
    eq_daily: pd.Series,
    eq_monthly: pd.Series,
    sku_profile: pd.DataFrame,
    abc_counts: pd.Series,
    segment_summary: pd.Series,
    output_path: Path,
) -> None:
    """生成包含关键图表的仪表盘图。"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("蜂巢智能拣选系统可视化总结", fontsize=16)

    if not eq_daily.empty:
        daily = eq_daily.tail(30)
        daily.index = pd.to_datetime(daily.index)
        axes[0, 0].plot(daily.index, daily.values, marker="o", linewidth=1.5)
        axes[0, 0].set_title("近30日订单量走势")
        axes[0, 0].set_xlabel("日期")
        axes[0, 0].set_ylabel("订单数")
        axes[0, 0].tick_params(axis="x", rotation=45)
    else:
        axes[0, 0].text(0.5, 0.5, "无订单数据", ha="center", va="center")
        axes[0, 0].set_axis_off()

    if not eq_monthly.empty:
        monthly = eq_monthly.copy()
        monthly.index = monthly.index.astype(str)
        axes[0, 1].bar(monthly.index, monthly.values, color="#4C78A8")
        period_count = len(monthly)
        axes[0, 1].set_title(f"近{period_count}月订单量对比")
        axes[0, 1].set_xlabel("月份")
        axes[0, 1].set_ylabel("订单数")
    else:
        axes[0, 1].text(0.5, 0.5, "无月度数据", ha="center", va="center")
        axes[0, 1].set_axis_off()

    if not sku_profile.empty and "total_quantity" in sku_profile:
        top_sku = sku_profile.nlargest(10, "total_quantity")
        axes[1, 0].barh(top_sku["pn_no"], top_sku["total_quantity"], color="#F58518")
        axes[1, 0].set_title("Top10 SKU 出库量")
        axes[1, 0].set_xlabel("出库数量")
        axes[1, 0].invert_yaxis()
    else:
        axes[1, 0].text(0.5, 0.5, "无 SKU 画像数据", ha="center", va="center")
        axes[1, 0].set_axis_off()

    axes[1, 1].set_title("ABC / 象限分布")
    if not abc_counts.empty:
        abc_counts = abc_counts.reindex(["A", "B", "C"], fill_value=0)
        axes[1, 1].pie(
            abc_counts.values,
            labels=abc_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=["#E45756", "#72B7B2", "#54A24B"],
        )
    else:
        axes[1, 1].text(0.5, 0.6, "无 ABC 数据", ha="center", va="center")

    if not segment_summary.empty:
        rect = axes[1, 1].inset_axes([0.05, -0.55, 0.9, 0.5])
        seg_order = ["高频高值", "高频低值", "低频高值", "低频低值"]
        segment_summary = segment_summary.reindex(seg_order, fill_value=0)
        x_pos = range(len(segment_summary))
        rect.bar(x_pos, segment_summary.values, color="#4C78A8")
        rect.set_xticks(list(x_pos))
        rect.set_xticklabels(segment_summary.index, rotation=20)
        rect.set_ylabel("SKU数")
        rect.set_title("EIQ-ABC 象限分布", fontsize=10)

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300)
    fig.savefig(output_path.with_suffix(".pdf"))
    plt.close(fig)


def export_plan_to_excel(sections: Dict[str, pd.DataFrame], output_path: Path) -> None:
    """将优化方案各板块导出为多 Sheet 的 Excel。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    try:
        writer = pd.ExcelWriter(output_path, engine="xlsxwriter")
    except ModuleNotFoundError:
        try:
            writer = pd.ExcelWriter(output_path, engine="openpyxl")
        except ModuleNotFoundError as error:
            print("[报告] 未安装 xlsxwriter/openpyxl，跳过 Excel 导出")
            return
    assert writer is not None
    with writer as excel_writer:
        for title, data in sections.items():
            if data is None:
                continue
            sheet_name = title[:31]
            if isinstance(data, pd.Series):
                data = data.to_frame(name="value")
            data.to_excel(excel_writer, sheet_name=sheet_name, index=False)


def export_plan_text(
    quality_report: pd.DataFrame,
    segment_summary: pd.Series,
    storage_plan: pd.DataFrame,
    strategy_table: pd.DataFrame,
    benefit_table: pd.DataFrame,
    output_path: Path,
) -> None:
    """生成包含关键优化要点的文本总结。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("蜂巢智能拣选系统优化方案总结\n")

    if not quality_report.empty:
        metrics = quality_report.set_index("指标")["值"].to_dict()
        lines.append("一、数据资产基础")
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    if not segment_summary.empty:
        lines.append("二、EIQ-ABC 象限规模")
        for segment, count in segment_summary.items():
            lines.append(f"- {segment}: {int(count)} 个 SKU")
        lines.append("")

    if not storage_plan.empty:
        lines.append("三、重点储位配置建议")
        for segment, group in storage_plan.groupby("matrix_segment"):
            skus = group["pn_no"].head(5).tolist()
            location = group["目标储位"].iloc[0]
            lines.append(f"- {segment}: 优先放置 SKU {', '.join(map(str, skus))}; 推荐储位 {location}")
        lines.append("")

    if not strategy_table.empty:
        lines.append("四、拣选策略分层")
        for _, row in strategy_table.iterrows():
            lines.append(f"- {row['象限']}: 策略 {row['method']}，优先级 {row['priority']}")
        lines.append("")

    if not benefit_table.empty and "value" in benefit_table.columns:
        benefits = benefit_table.reset_index().values.tolist()
        lines.append("五、效益评估")
        for metric, value in benefits:
            lines.append(f"- {metric}: {value}")
        lines.append("")

    with output_path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))
