"""EIQ-ABC 联合分析核心逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class MatrixConfig:
    frequency_col: str = "order_frequency"
    quantity_col: str = "quantity_share"
    abc_col: str = "abc_category"
    frequency_threshold: str = "median"  # 可替换成具体浮点阈值


def _resolve_frequency_threshold(values: pd.Series, threshold: str | float) -> float:
    if isinstance(threshold, (int, float)):
        return float(threshold)
    if threshold == "median":
        return float(values.median())
    if threshold == "mean":
        return float(values.mean())
    raise ValueError(f"未知的频次阈值配置: {threshold}")


def eiq_abc_matrix_analysis(
    eiq_df: pd.DataFrame,
    config: MatrixConfig | None = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """结合 EIQ 指标与 ABC 分类生成象限划分及概览。"""
    if eiq_df.empty:
        return eiq_df.copy(), pd.Series(dtype=int)
    cfg = config or MatrixConfig()
    work = eiq_df.copy()
    for col in (cfg.frequency_col, cfg.quantity_col, cfg.abc_col):
        if col not in work.columns:
            raise KeyError(f"缺少必要字段: {col}")
    threshold_value = _resolve_frequency_threshold(work[cfg.frequency_col], cfg.frequency_threshold)
    work["frequency_tier"] = np.where(work[cfg.frequency_col] >= threshold_value, "高频", "低频")

    def map_segment(row: pd.Series) -> str:
        if row["frequency_tier"] == "高频" and row[cfg.abc_col] == "A":
            return "高频高值"
        if row["frequency_tier"] == "高频":
            return "高频低值"
        if row[cfg.abc_col] == "A":
            return "低频高值"
        return "低频低值"

    work["matrix_segment"] = work.apply(map_segment, axis=1)
    segment_summary = work["matrix_segment"].value_counts().sort_index()
    return work, segment_summary


def generate_operational_guidance(
    matrix_df: pd.DataFrame,
    guidance_map: Dict[str, Dict[str, str]] | None = None,
) -> pd.DataFrame:
    """为不同象限附加储位、策略与路径建议。"""
    if matrix_df.empty:
        return matrix_df.copy()
    mapping = guidance_map or {
        "高频高值": {"储位建议": "黄金拣选位", "拣选策略": "批量拣选", "路径规划建议": "优先规划最短路径"},
        "高频低值": {"储位建议": "靠近主通道", "拣选策略": "波次拣选", "路径规划建议": "合并同向路径"},
        "低频高值": {"储位建议": "备用优先区", "拣选策略": "按单拣选", "路径规划建议": "结合价值优化"},
        "低频低值": {"储位建议": "边缘缓冲区", "拣选策略": "按单拣选", "路径规划建议": "批量合并减少触发"},
    }
    enriched = matrix_df.copy()
    for segment, advice in mapping.items():
        mask = enriched["matrix_segment"] == segment
        for column, text in advice.items():
            enriched.loc[mask, column] = text
    return enriched


def plot_quadrant_scatter(
    matrix_df: pd.DataFrame,
    config: MatrixConfig | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """绘制 EIQ-ABC 象限散点图。"""
    if matrix_df.empty:
        raise ValueError("象限数据为空，无法绘制")
    cfg = config or MatrixConfig()
    chart_ax = ax or plt.subplots(figsize=(8, 6))[1]
    colors = {"高频高值": "#d73027", "高频低值": "#fc8d59", "低频高值": "#91bfdb", "低频低值": "#4575b4"}
    markers = {"A": "o", "B": "s", "C": "^"}
    for (segment, abc), group in matrix_df.groupby(["matrix_segment", cfg.abc_col]):
        chart_ax.scatter(
            group[cfg.frequency_col],
            group[cfg.quantity_col],
            c=colors.get(segment, "#999999"),
            marker=markers.get(abc, "o"),
            s=80,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.6,
            label=f"{segment} / {abc}",
        )
    threshold_value = _resolve_frequency_threshold(matrix_df[cfg.frequency_col], cfg.frequency_threshold)
    chart_ax.axvline(threshold_value, color="gray", linestyle="--", linewidth=1)
    chart_ax.axhline(matrix_df[cfg.quantity_col].median(), color="gray", linestyle="--", linewidth=1)
    chart_ax.set_xlabel("订单频次占比")
    chart_ax.set_ylabel("数量占比")
    chart_ax.set_title("EIQ-ABC联合分析矩阵")
    chart_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="象限 / ABC等级")
    return chart_ax
