from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "weather_raw.json"
CLEAN_FILE = ROOT / "data" / "weather_clean.json"
META_FILE = ROOT / "data" / "weather_metadata.json"
FRONTEND_DATA_DIR = ROOT / "frontend" / "data"

WEATHER_TEXT = {
    0: "晴",
    1: "多云",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾",
    51: "小雨",
    53: "小雨",
    55: "中雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "阵雨",
    82: "强阵雨",
    95: "雷暴",
}


def value_at(values: list[Any], index: int, default: Any = None) -> Any:
    if index >= len(values):
        return default
    return values[index] if values[index] is not None else default


def season_of(month: int) -> str:
    if month in (3, 4, 5):
        return "春季"
    if month in (6, 7, 8):
        return "夏季"
    if month in (9, 10, 11):
        return "秋季"
    return "冬季"


def clean(payload: dict[str, Any]) -> list[dict[str, Any]]:
    daily = payload["daily"]
    rows: list[dict[str, Any]] = []
    for index, day in enumerate(daily["time"]):
        dt = datetime.fromisoformat(day)
        tmax = float(value_at(daily.get("temperature_2m_max", []), index, 0) or 0)
        tmin = float(value_at(daily.get("temperature_2m_min", []), index, 0) or 0)
        tmean = float(value_at(daily.get("temperature_2m_mean", []), index, (tmax + tmin) / 2) or 0)
        precipitation = float(value_at(daily.get("precipitation_sum", []), index, 0) or 0)
        snowfall = float(value_at(daily.get("snowfall_sum", []), index, 0) or 0)
        wind = float(value_at(daily.get("wind_speed_10m_max", []), index, 0) or 0)
        gust = float(value_at(daily.get("wind_gusts_10m_max", []), index, 0) or 0)
        code = int(value_at(daily.get("weather_code", []), index, 0) or 0)
        rows.append(
            {
                "date": day,
                "year": dt.year,
                "month": dt.month,
                "season": season_of(dt.month),
                "weather_code": code,
                "weather_text": WEATHER_TEXT.get(code, "其他"),
                "temp_max": round(tmax, 2),
                "temp_min": round(tmin, 2),
                "temp_mean": round(tmean, 2),
                "temp_range": round(tmax - tmin, 2),
                "apparent_max": round(float(value_at(daily.get("apparent_temperature_max", []), index, tmax) or tmax), 2),
                "apparent_min": round(float(value_at(daily.get("apparent_temperature_min", []), index, tmin) or tmin), 2),
                "precipitation": round(precipitation, 2),
                "rain": round(float(value_at(daily.get("rain_sum", []), index, precipitation) or 0), 2),
                "snowfall": round(snowfall, 2),
                "precipitation_hours": round(float(value_at(daily.get("precipitation_hours", []), index, 0) or 0), 2),
                "wind_max": round(wind, 2),
                "wind_gust": round(gust, 2),
                "radiation": round(float(value_at(daily.get("shortwave_radiation_sum", []), index, 0) or 0), 2),
                "is_hot": tmax >= 30,
                "is_cold": tmin <= -5,
                "is_rainy": precipitation >= 0.1,
                "is_heavy_rain": precipitation >= 25,
                "is_snowy": snowfall > 0,
                "is_windy": wind >= 38,
                "source": payload.get("source", "open-meteo"),
            }
        )
    return rows


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def build_metadata(rows: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    yearly: dict[int, dict[str, Any]] = defaultdict(lambda: {"temps": [], "rain": 0.0, "hot": 0, "cold": 0, "rainy": 0})
    monthly: dict[str, dict[str, Any]] = defaultdict(lambda: {"temps": [], "rain": 0.0, "days": 0})
    for row in rows:
        year = int(row["year"])
        month_key = f"{row['year']}-{int(row['month']):02d}"
        yearly[year]["temps"].append(float(row["temp_mean"]))
        yearly[year]["rain"] += float(row["precipitation"])
        yearly[year]["hot"] += int(bool(row["is_hot"]))
        yearly[year]["cold"] += int(bool(row["is_cold"]))
        yearly[year]["rainy"] += int(bool(row["is_rainy"]))
        monthly[month_key]["temps"].append(float(row["temp_mean"]))
        monthly[month_key]["rain"] += float(row["precipitation"])
        monthly[month_key]["days"] += 1

    weather_counts = Counter(row["weather_text"] for row in rows)
    meta = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "topic": "大连市近10年天气数据分析",
        "location": payload.get("location", {"name": "大连市"}),
        "source": payload.get("source", "open-meteo"),
        "source_url": payload.get("source_url", ""),
        "total_days": len(rows),
        "date_start": rows[0]["date"] if rows else "",
        "date_end": rows[-1]["date"] if rows else "",
        "avg_temp": average([float(row["temp_mean"]) for row in rows]),
        "max_temp": max((float(row["temp_max"]) for row in rows), default=0),
        "min_temp": min((float(row["temp_min"]) for row in rows), default=0),
        "total_precipitation": round(sum(float(row["precipitation"]) for row in rows), 2),
        "rainy_days": sum(1 for row in rows if row["is_rainy"]),
        "hot_days": sum(1 for row in rows if row["is_hot"]),
        "cold_days": sum(1 for row in rows if row["is_cold"]),
        "yearly": [
            {
                "year": year,
                "avg_temp": average(data["temps"]),
                "precipitation": round(data["rain"], 2),
                "hot_days": data["hot"],
                "cold_days": data["cold"],
                "rainy_days": data["rainy"],
            }
            for year, data in sorted(yearly.items())
        ],
        "monthly": [
            {
                "month": key,
                "avg_temp": average(data["temps"]),
                "precipitation": round(data["rain"], 2),
                "days": data["days"],
            }
            for key, data in sorted(monthly.items())
        ],
        "weather_counts": [{"name": name, "value": value} for name, value in weather_counts.most_common()],
        "note": "历史天气数据来自 Open-Meteo Archive API；若 source 为 demo-weather，则表示当前环境网络采集失败，使用本地生成的结构一致数据。",
    }
    return meta


def write_outputs(rows: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    clean_json = json.dumps(rows, ensure_ascii=False, indent=2)
    meta_json = json.dumps(meta, ensure_ascii=False, indent=2)
    data_script = f"window.WEATHER_DATA = {clean_json};\nwindow.WEATHER_META = {meta_json};\n"
    CLEAN_FILE.write_text(clean_json, encoding="utf-8")
    META_FILE.write_text(meta_json, encoding="utf-8")
    (ROOT / "data" / "weather_data.js").write_text(data_script, encoding="utf-8")
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (FRONTEND_DATA_DIR / "weather_clean.json").write_text(clean_json, encoding="utf-8")
    (FRONTEND_DATA_DIR / "weather_metadata.json").write_text(meta_json, encoding="utf-8")
    (FRONTEND_DATA_DIR / "weather_data.js").write_text(data_script, encoding="utf-8")


def main() -> None:
    payload = json.loads(RAW_FILE.read_text(encoding="utf-8-sig"))
    rows = clean(payload)
    meta = build_metadata(rows, payload)
    write_outputs(rows, meta)
    print(f"Processed {len(rows)} weather records to {CLEAN_FILE}")


if __name__ == "__main__":
    main()
