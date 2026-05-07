# Task2 作业4：Open-Meteo

一次请求获取福州大学旗山校区 2024 年天气数据。

位置：

- 经度：`119.198`
- 纬度：`26.05942`
- 时区：`Asia/Shanghai`

## 运行

```bash
python3 crawler.py
```

查看请求 URL：

```bash
python3 crawler.py --print-url
```

## 输出

- `data/hourly_weather.csv`：小时数据
- `data/daily_weather.csv`：每日数据
- `data/open_meteo_raw.json`：原始响应

题目里的 `cloud_cover_total` 在 Open-Meteo 接口中对应 `cloud_cover`，脚本输出 CSV 时改回题目字段名。
