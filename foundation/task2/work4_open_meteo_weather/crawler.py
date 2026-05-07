from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 26.05942
LONGITUDE = 119.198
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"
TIMEZONE = "Asia/Shanghai"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation_instant",
    "is_day",
]

DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "sunshine_duration",
]

HOURLY_CSV_COLUMNS = [
    "time",
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover_total",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation_instant",
    "is_day",
]

DAILY_CSV_COLUMNS = [
    "date",
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "sunshine_duration",
]

API_TO_HOURLY_CSV = {
    "cloud_cover": "cloud_cover_total",
}


def build_url() -> str:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(HOURLY_VARIABLES),
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": TIMEZONE,
    }
    return f"{API_URL}?{urlencode(params)}"


def fetch_weather_data(timeout: int = 60) -> dict[str, Any]:
    request = Request(build_url(), headers={"User-Agent": "learn-ai-weather-crawler/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"请求失败：HTTP {error.code} {message}") from error
    except URLError as error:
        raise RuntimeError(f"请求失败：{error.reason}") from error

    data = json.loads(body.decode("utf-8", errors="replace"))
    if data.get("error"):
        raise RuntimeError(f"Open-Meteo 返回错误：{data.get('reason')}")
    return data


def rows_from_series(series: dict[str, list[Any]], columns: list[str], time_key: str) -> list[dict[str, Any]]:
    times = series.get("time") or []
    rows: list[dict[str, Any]] = []
    for index, current_time in enumerate(times):
        row: dict[str, Any] = {time_key: current_time}
        for api_key, values in series.items():
            if api_key == "time":
                continue
            csv_key = API_TO_HOURLY_CSV.get(api_key, api_key)
            row[csv_key] = values[index] if index < len(values) else ""
        rows.append({column: row.get(column, "") for column in columns})
    return rows


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(data: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    hourly_rows = rows_from_series(data.get("hourly", {}), HOURLY_CSV_COLUMNS, "time")
    daily_rows = rows_from_series(data.get("daily", {}), DAILY_CSV_COLUMNS, "date")

    hourly_path = output_dir / "hourly_weather.csv"
    daily_path = output_dir / "daily_weather.csv"
    raw_path = output_dir / "open_meteo_raw.json"

    write_csv(hourly_path, HOURLY_CSV_COLUMNS, hourly_rows)
    write_csv(daily_path, DAILY_CSV_COLUMNS, daily_rows)
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return hourly_path, daily_path, raw_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一次请求获取福州大学旗山校区 2024 年 Open-Meteo 天气数据")
    parser.add_argument("--output-dir", default="data", help="输出目录")
    parser.add_argument("--print-url", action="store_true", help="只打印请求 URL，不发起请求")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.print_url:
        print(build_url())
        return

    data = fetch_weather_data()
    hourly_path, daily_path, raw_path = write_outputs(data, Path(args.output_dir))
    print(f"完成，一次请求已保存小时数据：{hourly_path.resolve()}")
    print(f"完成，一次请求已保存每日数据：{daily_path.resolve()}")
    print(f"原始响应已保存：{raw_path.resolve()}")
    print(f"小时记录数：{len(data.get('hourly', {}).get('time', []))}")
    print(f"每日记录数：{len(data.get('daily', {}).get('time', []))}")


if __name__ == "__main__":
    main()
