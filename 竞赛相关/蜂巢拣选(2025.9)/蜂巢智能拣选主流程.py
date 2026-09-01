"""蜂巢系统端到端分析流水线。"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from 蜂巢分析 import (
    BaselineMetrics,
    WarehouseLayout,
    abc_classification,
    calculate_eiq_metrics,
    cost_benefit_analysis,
    data_cleaning,
    eiq_abc_matrix_analysis,
    eq_analysis,
    export_plan_text,
    export_plan_to_excel,
    feature_engineering,
    generate_analysis_report,
    generate_operational_guidance,
    initialize_plot_style,
    render_visual_dashboard,
    picking_strategy_recommendation,
    plot_quadrant_scatter,
    save_report,
    storage_location_optimization,
    summarize_benefits,
)

DATABASE_PATH = Path(__file__).with_name("仓储数据集.sqlite")
OUTPUT_DIR = Path(__file__).parent / "output"


def load_orders(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"未找到数据库文件: {db_path}")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT pick_order_id, ship_id, row_no, pn_no, position, ship_num, "
            "ship_station, created_time, arr_city, createdate, uid FROM Picking_orders",
            conn,
        )
    df["ship_num"] = pd.to_numeric(df["ship_num"], errors="coerce").fillna(0)
    return df


def build_quality_report(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> pd.DataFrame:
    report = pd.DataFrame(
        {
            "指标": ["原始记录数", "清洗后记录数", "缺失值总数", "唯一订单数", "唯一SKU数"],
            "值": [
                len(raw_df),
                len(clean_df),
                int(raw_df.isna().sum().sum()),
                raw_df["pick_order_id"].nunique(),
                raw_df["pn_no"].nunique(),
            ],
        }
    )
    return report


def derive_layout(clean_df: pd.DataFrame) -> WarehouseLayout:
    positions = [
        pos
        for pos in clean_df.get("position", pd.Series(dtype=str)).dropna().unique()
        if pos not in ("未知", "")
    ]
    golden = positions[:10] or ["GZ-1"]
    reserve = positions[10:25] or golden
    edge = positions[25:] or reserve
    return WarehouseLayout(golden_zone=golden, reserve_zone=reserve, edge_zone=edge)


def simulate_benefits(segment_summary: Dict[str, int], total_orders: int) -> pd.DataFrame:
    total_sku = sum(segment_summary.values()) or 1
    high_value_ratio = segment_summary.get("高频高值", 0) / total_sku
    high_freq_ratio = (
        segment_summary.get("高频高值", 0) + segment_summary.get("高频低值", 0)
    ) / total_sku
    baseline = BaselineMetrics(
        walking_distance=total_orders * 1.0,
        picking_time=total_orders * 0.5,
        labor_cost=total_orders * 0.2,
        throughput=total_orders / 100.0,
    )
    after = BaselineMetrics(
        walking_distance=baseline.walking_distance * (1 - min(0.3, high_value_ratio * 0.2)),
        picking_time=baseline.picking_time * (1 - min(0.25, high_freq_ratio * 0.15)),
        labor_cost=baseline.labor_cost * (1 - min(0.2, high_value_ratio * 0.1)),
        throughput=baseline.throughput * (1 + min(0.3, high_freq_ratio * 0.2)),
    )
    benefit_metrics = cost_benefit_analysis(baseline, after)
    return summarize_benefits(benefit_metrics)


def prepare_recent_months(monthly_series: pd.Series, months: int = 6) -> pd.Series:
    if monthly_series.empty:
        return monthly_series
    work = monthly_series.copy()
    if not isinstance(work.index, pd.PeriodIndex):
        period_index = pd.to_datetime(work.index, errors="coerce").to_period("M")
        work = pd.Series(work.to_numpy(), index=period_index, name=work.name)
    work = work.sort_index()
    if months:
        work = work.tail(months)
    work.index.name = work.index.name or "月份"
    return work


def run_pipeline(db_path: Path = DATABASE_PATH) -> None:
    font_used = initialize_plot_style()
    if font_used:
        print(f"[字体] 已应用中文字体: {font_used}")
    else:
        print("[字体] 未找到中文字体，将使用默认字体 (可能出现乱码)")

    print("[1] 读取原始订单数据...")
    raw_orders = load_orders(db_path)

    print("[2] 数据预处理与特征工程...")
    cleaned_orders = data_cleaning(raw_orders)
    order_features, sku_features = feature_engineering(cleaned_orders)
    quality_report = build_quality_report(raw_orders, cleaned_orders)

    print("[3] EIQ 指标分析...")
    eq_daily, eq_monthly = eq_analysis(cleaned_orders)
    eq_monthly_recent = prepare_recent_months(eq_monthly)
    eiq_metrics = calculate_eiq_metrics(cleaned_orders)

    print("[4] ABC 分类与 EIQ-ABC 联合分析...")
    classified = abc_classification(eiq_metrics)
    matrix_df, segment_summary = eiq_abc_matrix_analysis(classified)
    recommendations = generate_operational_guidance(matrix_df)
    abc_counts = classified["abc_category"].value_counts()

    print("[5] 优化策略生成...")
    layout = derive_layout(cleaned_orders)
    storage_plan = storage_location_optimization(recommendations, layout)
    strategy_plan = picking_strategy_recommendation(recommendations)

    print("[6] 成本效益模拟...")
    benefit_table = simulate_benefits(segment_summary.to_dict(), len(cleaned_orders))

    print("[7] 生成分析报告...")
    strategy_table = pd.DataFrame(
        [(seg, info["method"], info["priority"]) for seg, info in strategy_plan.items()],
        columns=["象限", "method", "priority"],
    )
    eq_daily_df = eq_daily.reset_index()
    eq_daily_df.columns = ["日期", "订单数"]
    eq_monthly_df = eq_monthly_recent.reset_index()
    eq_monthly_df.columns = ["月份", "订单数"]
    eq_monthly_df["月份"] = eq_monthly_df["月份"].astype(str)
    sections = {
        "数据质量报告": quality_report,
        "订单特征画像": order_features.head(10),
        "SKU特征画像": sku_features.head(10),
        "EIQ指标": eiq_metrics.head(10),
        "ABC分类": classified.head(10),
        "订单量趋势(日)": eq_daily_df.tail(14),
    "订单量趋势(月)": eq_monthly_df,
        "联合分析建议": recommendations.head(10),
        "储位方案": storage_plan[["pn_no", "matrix_segment", "目标储位"]].head(10),
        "拣选策略": strategy_table,
        "成本效益": benefit_table,
    }
    report = generate_analysis_report(sections)
    OUTPUT_DIR.mkdir(exist_ok=True)
    save_report(report, OUTPUT_DIR / "honeycomb_report.csv")

    segment_summary_df = segment_summary.rename_axis("matrix_segment").reset_index(name="sku_count")
    abc_counts_df = abc_counts.rename_axis("abc_category").reset_index(name="sku_count")
    plan_sections = {
        "数据质量报告": quality_report,
        "订单特征画像": order_features,
        "SKU特征画像": sku_features,
        "EIQ指标": eiq_metrics,
        "ABC分类": classified,
        "订单量趋势(日)": eq_daily_df,
        "订单量趋势(月)": eq_monthly_df,
        "联合分析建议": recommendations,
        "储位方案": storage_plan,
        "拣选策略": strategy_table,
        "象限汇总": segment_summary_df,
        "ABC分布": abc_counts_df,
        "成本效益": benefit_table,
    }
    export_plan_to_excel(plan_sections, OUTPUT_DIR / "honeycomb_plan.xlsx")
    export_plan_text(
        quality_report,
        segment_summary,
        storage_plan,
        strategy_table,
        benefit_table,
        OUTPUT_DIR / "honeycomb_plan.txt",
    )

    print("[8] 可视化输出...")
    plot_ax = plot_quadrant_scatter(recommendations)
    plot_ax.figure.tight_layout()
    matrix_plot_path = OUTPUT_DIR / "eiq_abc_matrix.png"
    plot_ax.figure.savefig(matrix_plot_path, dpi=300)
    plt.close(plot_ax.figure)
    render_visual_dashboard(
        eq_daily,
        eq_monthly_recent,
        sku_features,
        abc_counts,
        segment_summary,
        OUTPUT_DIR / "honeycomb_dashboard.png",
    )

    print("流水线执行完成，关键输出已保存至 output/ 目录。")


if __name__ == "__main__":
    run_pipeline()
