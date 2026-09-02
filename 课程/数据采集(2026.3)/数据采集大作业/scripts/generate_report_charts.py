from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MaxNLocator

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - optional preview image only
    Image = ImageDraw = ImageFont = None


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "weather_clean.json"
META_FILE = ROOT / "data" / "weather_metadata.json"
OUT_DIR = ROOT / "report_charts"


def chinese_font() -> FontProperties:
    for path in (
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ):
        if path.exists():
            return FontProperties(fname=str(path))
    return FontProperties()


FONT = chinese_font()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120


def setup_axis(ax, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, fontproperties=FONT, fontsize=18, pad=14, weight="bold")
    ax.set_xlabel(xlabel, fontproperties=FONT, fontsize=12)
    ax.set_ylabel(ylabel, fontproperties=FONT, fontsize=12)
    ax.grid(True, axis="y", color="#d9e2ec", linewidth=0.9, alpha=0.9)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)
        label.set_fontsize(10)


def save_chart(fig, name: str) -> Path:
    fig.tight_layout()
    path = OUT_DIR / name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def season_summary(rows: list[dict]) -> tuple[list[str], list[float], list[float]]:
    order = ["春季", "夏季", "秋季", "冬季"]
    data = defaultdict(lambda: {"temps": [], "rain": 0.0})
    for row in rows:
        item = data[row["season"]]
        item["temps"].append(float(row["temp_mean"]))
        item["rain"] += float(row["precipitation"])
    temps = [sum(data[name]["temps"]) / len(data[name]["temps"]) for name in order]
    rain = [data[name]["rain"] for name in order]
    return order, temps, rain


def generate_overview(paths: list[Path]) -> Path | None:
    if Image is None or ImageDraw is None or ImageFont is None:
        return None

    images = [Image.open(path).convert("RGB") for path in paths]
    thumb_width = 720
    thumbs = []
    for image in images:
        scale = thumb_width / image.width
        thumbs.append(image.resize((thumb_width, int(image.height * scale))))

    cols = 2
    pad = 28
    title_height = 72
    row_count = (len(thumbs) + cols - 1) // cols
    row_heights = [
        max(thumbs[index].height for index in range(row * cols, min((row + 1) * cols, len(thumbs))))
        for row in range(row_count)
    ]
    canvas_width = cols * thumb_width + (cols + 1) * pad
    canvas_height = title_height + sum(row_heights) + (row_count + 1) * pad
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    title_font = ImageFont.truetype(str(font_path), 34) if font_path.exists() else ImageFont.load_default()
    draw.text((pad, 22), "大连市近10年天气数据分析图表总览", fill="#1f2933", font=title_font)

    y = title_height + pad
    index = 0
    for row_height in row_heights:
        x = pad
        for _ in range(cols):
            if index >= len(thumbs):
                break
            canvas.paste(thumbs[index], (x, y))
            x += thumb_width + pad
            index += 1
        y += row_height + pad

    overview = OUT_DIR / "00_charts_overview.png"
    canvas.save(overview, quality=95)
    return overview


def main() -> None:
    rows = json.loads(DATA_FILE.read_text(encoding="utf-8-sig"))
    meta = json.loads(META_FILE.read_text(encoding="utf-8-sig"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in OUT_DIR.glob("*.png"):
        old_file.unlink()

    yearly = meta["yearly"]
    years = [int(item["year"]) for item in yearly]
    avg_temp = [float(item["avg_temp"]) for item in yearly]
    year_rain = [float(item["precipitation"]) for item in yearly]

    monthly = meta["monthly"]
    months = [item["month"] for item in monthly]
    month_temp = [float(item["avg_temp"]) for item in monthly]
    month_rain = [float(item["precipitation"]) for item in monthly]

    season_names, season_temp, season_rain = season_summary(rows)
    paths: list[Path] = []

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.plot(years, avg_temp, color="#2f80ed", marker="o", linewidth=2.8, markersize=6)
    for x, y in zip(years, avg_temp):
        ax.text(x, y + 0.15, f"{y:.1f}", ha="center", va="bottom", fontproperties=FONT, fontsize=9)
    setup_axis(ax, "大连市近10年年均气温趋势", "年份", "平均气温（°C）")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    paths.append(save_chart(fig, "01_year_avg_temp.png"))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    colors = ["#77b7df" if value < max(year_rain) else "#f2994a" for value in year_rain]
    ax.bar(years, year_rain, color=colors, width=0.62)
    for x, y in zip(years, year_rain):
        ax.text(x, y + max(year_rain) * 0.015, f"{y:.0f}", ha="center", va="bottom", fontproperties=FONT, fontsize=9)
    setup_axis(ax, "大连市近10年年降水量对比", "年份", "降水量（mm）")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    paths.append(save_chart(fig, "02_year_precipitation.png"))

    fig, ax1 = plt.subplots(figsize=(14, 6.4))
    x_values = list(range(len(months)))
    ax1.bar(x_values, month_rain, color="#9bd0f5", width=0.8, label="月降水量")
    ax1.set_ylabel("降水量（mm）", fontproperties=FONT, fontsize=12)
    ax2 = ax1.twinx()
    ax2.plot(x_values, month_temp, color="#d94f45", linewidth=2.0, label="月均气温")
    ax2.set_ylabel("平均气温（°C）", fontproperties=FONT, fontsize=12)
    step = max(1, len(months) // 18)
    ax1.set_xticks(x_values[::step])
    ax1.set_xticklabels([months[index] for index in x_values[::step]], rotation=45, ha="right", fontproperties=FONT, fontsize=9)
    ax1.set_title("大连市月均气温与月降水量变化", fontproperties=FONT, fontsize=18, pad=14, weight="bold")
    ax1.grid(True, axis="y", color="#d9e2ec", linewidth=0.9)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    for label in ax1.get_yticklabels() + ax2.get_yticklabels():
        label.set_fontproperties(FONT)
    handles, labels = [], []
    for current_ax in (ax1, ax2):
        current_handles, current_labels = current_ax.get_legend_handles_labels()
        handles += current_handles
        labels += current_labels
    ax1.legend(handles, labels, prop=FONT, loc="upper left", frameon=False)
    paths.append(save_chart(fig, "03_monthly_temp_precipitation.png"))

    season_colors = ["#65b96d", "#f2c94c", "#f2994a", "#56a0d3"]
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    ax.bar(season_names, season_temp, color=season_colors, width=0.55)
    for name, value in zip(season_names, season_temp):
        ax.text(name, value + (0.35 if value >= 0 else -0.75), f"{value:.2f}°C", ha="center", fontproperties=FONT, fontsize=11)
    setup_axis(ax, "大连市四季平均气温对比", "季节", "平均气温（°C）")
    paths.append(save_chart(fig, "04_season_avg_temp.png"))

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    ax.bar(season_names, season_rain, color=season_colors, width=0.55)
    for name, value in zip(season_names, season_rain):
        ax.text(name, value + max(season_rain) * 0.018, f"{value:.0f}mm", ha="center", fontproperties=FONT, fontsize=11)
    setup_axis(ax, "大连市四季累计降水量对比", "季节", "降水量（mm）")
    paths.append(save_chart(fig, "05_season_precipitation.png"))

    weather_counts = meta["weather_counts"]
    top_weather = weather_counts[:7]
    other_count = sum(int(item["value"]) for item in weather_counts[7:])
    labels = [item["name"] for item in top_weather] + (["其他"] if other_count else [])
    values = [int(item["value"]) for item in top_weather] + ([other_count] if other_count else [])
    fig, ax = plt.subplots(figsize=(8.8, 7.2))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=120,
        colors=["#4e79a7", "#76b7b2", "#59a14f", "#edc948", "#f28e2b", "#e15759", "#b07aa1", "#bab0ab"],
        pctdistance=0.75,
        textprops={"fontproperties": FONT, "fontsize": 10},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")
        autotext.set_fontproperties(FONT)
    ax.set_title("大连市近10年天气类型占比", fontproperties=FONT, fontsize=18, pad=14, weight="bold")
    ax.axis("equal")
    paths.append(save_chart(fig, "06_weather_type_share.png"))

    extreme_labels = ["高温日", "低温日", "降水日", "大雨日", "大风日", "降雪日"]
    extreme_values = [
        sum(1 for row in rows if row["is_hot"]),
        sum(1 for row in rows if row["is_cold"]),
        sum(1 for row in rows if row["is_rainy"]),
        sum(1 for row in rows if row["is_heavy_rain"]),
        sum(1 for row in rows if row["is_windy"]),
        sum(1 for row in rows if row["is_snowy"]),
    ]
    fig, ax = plt.subplots(figsize=(9.8, 5.8))
    ax.bar(extreme_labels, extreme_values, color=["#e15759", "#4e79a7", "#59a14f", "#f28e2b", "#b07aa1", "#76b7b2"], width=0.58)
    for name, value in zip(extreme_labels, extreme_values):
        ax.text(name, value + max(extreme_values) * 0.018, str(value), ha="center", fontproperties=FONT, fontsize=11)
    setup_axis(ax, "大连市近10年极端天气日统计", "类型", "天数")
    paths.append(save_chart(fig, "07_extreme_weather_days.png"))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    top10 = weather_counts[:10]
    y_labels = [item["name"] for item in top10][::-1]
    x_values = [int(item["value"]) for item in top10][::-1]
    ax.barh(y_labels, x_values, color="#6aaed6")
    for name, value in zip(y_labels, x_values):
        ax.text(value + max(x_values) * 0.01, name, str(value), va="center", fontproperties=FONT, fontsize=10)
    setup_axis(ax, "大连市近10年主要天气类型出现天数", "天数", "")
    paths.append(save_chart(fig, "08_weather_type_days.png"))

    overview = generate_overview(paths)
    if overview:
        paths.insert(0, overview)

    print(f"Saved {len(paths)} chart images to {OUT_DIR}")


if __name__ == "__main__":
    main()
