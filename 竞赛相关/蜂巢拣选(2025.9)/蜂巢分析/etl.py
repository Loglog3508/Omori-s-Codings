"""数据预处理与特征工程模块。"""

from __future__ import annotations

from typing import Tuple

import pandas as pd


def data_cleaning(raw_data: pd.DataFrame) -> pd.DataFrame:
    """清洗原始数据，处理缺失值、重复行与数据类型。"""
    if raw_data.empty:
        return raw_data.copy()
    cleaned = raw_data.drop_duplicates()
    numeric_cols = cleaned.select_dtypes(include=["int64", "float64"]).columns
    cleaned[numeric_cols] = cleaned[numeric_cols].fillna(0)
    cleaned = cleaned.fillna({col: "未知" for col in cleaned.select_dtypes(include="object").columns})
    date_cols = [col for col in cleaned.columns if "time" in col.lower() or "date" in col.lower()]
    for col in date_cols:
        cleaned[col] = pd.to_datetime(cleaned[col], errors="coerce")
    return cleaned


def feature_engineering(clean_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """构造订单与 SKU 维度的衍生特征。"""
    if clean_data.empty:
        return clean_data.copy(), pd.DataFrame()
    orders = clean_data.groupby("pick_order_id").agg(
        sku_lines=("pn_no", "nunique"),
        total_quantity=("ship_num", "sum"),
    )
    sku_profile = clean_data.groupby("pn_no").agg(
        order_count=("pick_order_id", "nunique"),
        total_quantity=("ship_num", "sum"),
    )
    return orders, sku_profile.reset_index()
