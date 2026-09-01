"""EIQ 指标分析模块。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd


@dataclass(frozen=True)
class EIQConfig:
    order_col: str = "pick_order_id"
    sku_col: str = "pn_no"
    quantity_col: str = "ship_num"
    created_time_col: str = "created_time"
    position_col: str | None = "position"
    station_col: str | None = "ship_station"
    city_col: str | None = "arr_city"


def calculate_eiq_metrics(df: pd.DataFrame, config: EIQConfig | None = None) -> pd.DataFrame:
    """汇总订单频次、SKU 数量占比等核心指标。"""
    cfg = config or EIQConfig()
    work = df.copy()
    for column in (cfg.order_col, cfg.sku_col, cfg.quantity_col):
        if column not in work.columns:
            raise KeyError(f"缺少必要字段: {column}")
    total_orders = work[cfg.order_col].nunique()
    total_quantity = work[cfg.quantity_col].sum()
    aggregations = {
        "order_count": (cfg.order_col, "nunique"),
        "line_count": (cfg.sku_col, "count"),
        "total_quantity": (cfg.quantity_col, "sum"),
        "mean_quantity": (cfg.quantity_col, "mean"),
    }
    if cfg.position_col and cfg.position_col in work.columns:
        aggregations["position_count"] = (cfg.position_col, "nunique")
    if cfg.station_col and cfg.station_col in work.columns:
        aggregations["station_count"] = (cfg.station_col, "nunique")
    if cfg.city_col and cfg.city_col in work.columns:
        aggregations["city_count"] = (cfg.city_col, "nunique")
    metrics = work.groupby(cfg.sku_col).agg(**aggregations)
    metrics["order_frequency"] = metrics["order_count"] / total_orders if total_orders else 0
    metrics["quantity_share"] = metrics["total_quantity"] / total_quantity if total_quantity else 0
    return metrics.reset_index()


def eq_analysis(df: pd.DataFrame, config: EIQConfig | None = None) -> Tuple[pd.Series, pd.Series]:
    cfg = config or EIQConfig()
    if cfg.created_time_col not in df.columns:
        raise KeyError(f"缺少必要字段: {cfg.created_time_col}")
    orders = df[[cfg.order_col, cfg.created_time_col]].dropna()
    orders[cfg.created_time_col] = pd.to_datetime(orders[cfg.created_time_col], errors="coerce")
    orders = orders.dropna(subset=[cfg.created_time_col])
    orders["date"] = orders[cfg.created_time_col].dt.date
    daily_counts = orders.groupby("date")[cfg.order_col].nunique().sort_index()
    monthly_counts = orders.groupby(orders[cfg.created_time_col].dt.to_period("M"))[cfg.order_col].nunique()
    return daily_counts, monthly_counts


def en_analysis(df: pd.DataFrame, config: EIQConfig | None = None) -> pd.Series:
    cfg = config or EIQConfig()
    line_counts = df.groupby(cfg.order_col)[cfg.sku_col].nunique()
    return line_counts.sort_values(ascending=False)


def iq_analysis(df: pd.DataFrame, config: EIQConfig | None = None) -> pd.Series:
    cfg = config or EIQConfig()
    return df.groupby(cfg.sku_col)[cfg.quantity_col].sum().sort_values(ascending=False)


def ik_analysis(df: pd.DataFrame, config: EIQConfig | None = None) -> pd.Series:
    cfg = config or EIQConfig()
    return df.groupby(cfg.sku_col)[cfg.order_col].nunique().sort_values(ascending=False)
