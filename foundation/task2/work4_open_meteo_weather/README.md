# Task 2 作业 4：Open-Meteo 天气数据

本作业通过 Open-Meteo Historical Weather API，一次请求获取福州大学旗山校区 2024 年 1 月至 12 月的天气数据，并保存为 CSV。

请求位置：

- 经度：`119.198`
- 纬度：`26.05942`
- 时区：`Asia/Shanghai`
- 日期：`2024-01-01` 至 `2024-12-31`

## 输出内容

脚本只发起一次网络请求，然后从同一个 JSON 响应里拆出两个 CSV：

- `data/hourly_weather.csv`：每小时天气变量
- `data/daily_weather.csv`：每日天气变量
- `data/open_meteo_raw.json`：Open-Meteo 原始响应，方便检查

## 小时变量

- `temperature_2m`：温度，2 米
- `relative_humidity_2m`：相对湿度，2 米
- `apparent_temperature`：体感温度
- `precipitation`：降水
- `weather_code`：天气代码
- `cloud_cover_total`：总云量
- `wind_speed_10m`：风速，10 米
- `wind_direction_10m`：风向，10 米
- `shortwave_radiation_instant`：短波太阳辐射 GHI，即时
- `is_day`：是否白天

说明：Open-Meteo 当前接口中的总云量字段名是 `cloud_cover`，脚本请求该字段后，在 CSV 中按题目要求保存为 `cloud_cover_total`。

## 每日变量

- `temperature_2m_mean`：平均温度，2 米
- `temperature_2m_max`：最高温度，2 米
- `temperature_2m_min`：最低温度，2 米
- `precipitation_sum`：降水量
- `sunshine_duration`：日照时长

## 运行方式

进入本目录：

```bash
cd foundation/task2/work4_open_meteo_weather
```

运行脚本：

```bash
python3 crawler.py
```

如果只想查看这一次请求的 URL：

```bash
python3 crawler.py --print-url
```

## 注意

作业要求“只允许发起一次请求”。脚本运行时只调用一次 Open-Meteo API，小时 CSV、每日 CSV 和原始 JSON 都来自这一次响应。
