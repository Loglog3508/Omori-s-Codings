"""仓储优化策略模块。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


@dataclass(frozen=True)
class WarehouseLayout:
    golden_zone: List[str]
    reserve_zone: List[str]
    edge_zone: List[str]


def storage_location_optimization(quadrant_data: pd.DataFrame, layout: WarehouseLayout) -> pd.DataFrame:
    """根据象限结果匹配储位区域。"""
    if quadrant_data.empty:
        return quadrant_data.copy()
    zone_map = {
        "高频高值": layout.golden_zone,
        "高频低值": layout.golden_zone + layout.reserve_zone,
        "低频高值": layout.reserve_zone,
        "低频低值": layout.edge_zone,
    }
    result = quadrant_data.copy()
    result["目标储位"] = result["matrix_segment"].map(lambda seg: zone_map.get(seg, layout.edge_zone))
    return result


def picking_strategy_recommendation(quadrant_data: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """输出象限到拣选策略的映射。"""
    strategies = {
        "高频高值": {"method": "batch_picking", "priority": "highest"},
        "高频低值": {"method": "wave_picking", "priority": "high"},
        "低频高值": {"method": "single_order", "priority": "high"},
        "低频低值": {"method": "single_order", "priority": "medium"},
    }
    return {seg: strategies.get(seg, {"method": "single_order", "priority": "medium"}) for seg in quadrant_data["matrix_segment"].unique()}


def path_optimization(orders: pd.DataFrame, layout_mapping: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
    """基于简易距离模型输出拣货路径建议。"""
    if orders.empty:
        return orders.copy()
    if not layout_mapping:
        raise ValueError("缺少储位坐标映射")
    sequences = []
    for order_id, group in orders.groupby("pick_order_id"):
        if "position" in group.columns:
            positions = group["position"].fillna("未指定").tolist()
        else:
            positions = []
        coords = [layout_mapping.get(position, (0.0, 0.0)) for position in positions]
        cumulative = 0.0
        last = None
        for coord in coords:
            if last is not None:
                cumulative += ((coord[0] - last[0]) ** 2 + (coord[1] - last[1]) ** 2) ** 0.5
            last = coord
        sequences.append({"pick_order_id": order_id, "estimated_distance": round(cumulative, 2)})
    return pd.DataFrame(sequences)
