import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from 蜂巢分析 import abc_classification, calculate_eiq_metrics, eiq_abc_matrix_analysis

DATABASE_PATH = Path(__file__).with_name("仓储数据集.sqlite")


def load_picking_orders(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"未找到数据库文件: {db_path}")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT pick_order_id, pn_no, ship_num, ship_station FROM Picking_orders",
            conn,
        )
    df.columns = [col.strip() for col in df.columns]
    column_map = {col.lower(): col for col in df.columns}
    station_source = (
        column_map.get("ship_station")
        or column_map.get("shipstation")
        or column_map.get("station")
    )
    if station_source and station_source != "ship_station":
        df = df.rename(columns={station_source: "ship_station"})
    if "ship_station" not in df.columns:
        df["ship_station"] = "未指定工位"
    df = df.dropna(subset=["pn_no"]).copy()
    df["ship_num"] = pd.to_numeric(df["ship_num"], errors="coerce").fillna(0)
    df["ship_station"] = df["ship_station"].fillna("未指定工位").astype(str)
    return df

def create_station_segment_pivot(picking_df: pd.DataFrame, joint_matrix: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    merged = picking_df.merge(joint_matrix[["pn_no", "matrix_segment"]], on="pn_no", how="inner")
    if merged.empty:
        return pd.DataFrame()
    segment_pivot = merged.pivot_table(
        index="ship_station",
        columns="matrix_segment",
        values="ship_num",
        aggfunc="sum",
        fill_value=0,
    )
    total_volume = segment_pivot.sum(axis=1)
    top_index = total_volume.sort_values(ascending=False).head(top_n).index
    segment_pivot = segment_pivot.loc[top_index]
    segment_pivot = segment_pivot.reindex(columns=["高频高值", "高频低值", "低频高值", "低频低值"], fill_value=0)
    return segment_pivot


def plot_heatmap(pivot_df: pd.DataFrame) -> None:
    if pivot_df.empty:
        print("缺少可视化数据，无法绘制热力图。")
        return
    plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8, 6))
    data = pivot_df.to_numpy()
    im = ax.imshow(data, cmap="YlOrRd")
    ax.set_xticks(range(data.shape[1]))
    ax.set_xticklabels(pivot_df.columns)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels(pivot_df.index)
    ax.set_xlabel("EIQ-ABC象限")
    ax.set_ylabel("拣选工位 (ship_station)")
    ax.set_title("拣选工位与EIQ-ABC象限热力图 (按发货数量汇总)")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.0f}", ha="center", va="center", color="black", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.8, label="发货数量")
    fig.tight_layout()
    plt.show()


def main() -> None:
    try:
        picking_orders = load_picking_orders(DATABASE_PATH)
        print("载入字段:", picking_orders.columns.tolist())
        eiq_metrics = calculate_eiq_metrics(picking_orders)
        classified = abc_classification(eiq_metrics)
        joint_matrix, _ = eiq_abc_matrix_analysis(classified)
        pivot_df = create_station_segment_pivot(picking_orders, joint_matrix)
        print("拣选工位与象限分布 (Top 10 工位，按发货数量)：")
        print(pivot_df.to_string())
        plot_heatmap(pivot_df)
    except FileNotFoundError as exc:
        print(exc)
    except sqlite3.Error as exc:
        print(f"数据库读取错误: {exc}")
    except Exception as exc:
        print(f"分析失败: {exc}")


if __name__ == "__main__":
    main()
