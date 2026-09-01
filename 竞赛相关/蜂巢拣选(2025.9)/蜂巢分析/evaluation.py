"""成本效益分析模块。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass(frozen=True)
class BaselineMetrics:
    walking_distance: float
    picking_time: float
    labor_cost: float
    throughput: float


def cost_benefit_analysis(before: BaselineMetrics, after: BaselineMetrics) -> Dict[str, float]:
    """比较优化前后的关键指标并输出节省比例。"""
    def saving_ratio(original: float, new: float) -> float:
        if original == 0:
            return 0.0
        return round((original - new) / original, 4)

    return {
        "walking_distance_reduction": saving_ratio(before.walking_distance, after.walking_distance),
        "time_savings": saving_ratio(before.picking_time, after.picking_time),
        "labor_cost_reduction": saving_ratio(before.labor_cost, after.labor_cost),
        "throughput_improvement": round(after.throughput - before.throughput, 4),
    }


def summarize_benefits(report: Dict[str, float]) -> pd.DataFrame:
    """将节省指标转为表格化结果，便于报告生成。"""
    return pd.DataFrame.from_dict(report, orient="index", columns=["value"])
