from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "weather_raw.json"

DALIAN = {
    "name": "大连市",
    "latitude": 38.914,
    "longitude": 121.6147,
    "timezone": "Asia/Shanghai",
}

DAILY_FIELDS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "shortwave_radiation_sum",
]


def default_range() -> tuple[str, str]:
    end = date.today() - timedelta(days=7)
    start = end.replace(year=end.year - 10) + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def collect_weather(start_date: str, end_date: str) -> dict[str, Any]:
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": DALIAN["latitude"],
            "longitude": DALIAN["longitude"],
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(DAILY_FIELDS),
            "timezone": DALIAN["timezone"],
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "cell_selection": "land",
        },
        headers={"User-Agent": "Mozilla/5.0 weather-analysis-course-project"},
        timeout=60,
    )
    try:
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        preview = response.text[:160].replace("\n", " ").strip()
        raise RuntimeError(f"Open-Meteo API failed. HTTP {response.status_code}. Preview: {preview}") from exc
    if "daily" not in payload or "time" not in payload["daily"]:
        raise RuntimeError("Open-Meteo response does not contain daily weather data")
    payload["location"] = DALIAN
    payload["source"] = "open-meteo"
    payload["source_url"] = response.url
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()
    start_date, end_date = default_range()
    if args.start_date:
        start_date = args.start_date
    if args.end_date:
        end_date = args.end_date
    try:
        payload = collect_weather(start_date, end_date)
        RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
        RAW_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved weather raw data to {RAW_FILE}")
        print(f"Range: {start_date} to {end_date}; days: {len(payload['daily']['time'])}")
    except Exception as exc:
        print(f"Weather collection failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
