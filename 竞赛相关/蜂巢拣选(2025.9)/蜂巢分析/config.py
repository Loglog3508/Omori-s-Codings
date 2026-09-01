"""系统配置模块。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class SystemConfig:
    abc_thresholds: Tuple[float, float, float] = (0.7, 0.9, 1.0)
    ik_threshold: str = "median"
    warehouse_constraints: Dict[str, float] | None = None


def default_config() -> SystemConfig:
    """返回默认系统配置。"""
    return SystemConfig(warehouse_constraints={"max_capacity": 1.0, "safety_stock": 0.1})
