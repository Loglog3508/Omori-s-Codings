"""ABC 分类模块。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

import pandas as pd


@dataclass(frozen=True)
class ABCConfig:
    value_method: Literal["quantity", "value"] = "quantity"
    quantity_col: str = "total_quantity"
    value_col: str = "total_value"
    sku_col: str = "pn_no"
    thresholds: Tuple[float, float, float] = (0.7, 0.9, 1.0)


def abc_classification(df: pd.DataFrame, config: ABCConfig | None = None) -> pd.DataFrame:
    cfg = config or ABCConfig()
    column = cfg.quantity_col if cfg.value_method == "quantity" else cfg.value_col
    if column not in df.columns:
        raise KeyError(f"缺少必要字段: {column}")
    ranked = df.sort_values(column, ascending=False).reset_index(drop=True)
    total_value = ranked[column].sum()
    if total_value == 0:
        return ranked.assign(abc_category="C", cum_share=0)
    ranked["cum_share"] = ranked[column].cumsum() / total_value
    low, mid, _ = cfg.thresholds
    ranked["abc_category"] = "C"
    ranked.loc[ranked["cum_share"] <= low, "abc_category"] = "A"
    ranked.loc[(ranked["cum_share"] > low) & (ranked["cum_share"] <= mid), "abc_category"] = "B"
    return ranked