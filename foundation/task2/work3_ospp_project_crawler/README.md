# Task2 作业3：开源之夏项目

通过开源之夏官网接口获取项目列表和项目详情。

用到的接口：

- `/api/getProList`
- `/api/getProDetail`
- `/api/publicApplication`

## 运行

```bash
python3 crawler.py --limit 20
```

下载申请书 PDF：

```bash
python3 crawler.py --limit 5 --download-applications
```

抓取全部项目：

```bash
python3 crawler.py --limit 0
```

## 输出

- `data/projects.csv`
- `data/projects.json`
- `data/raw_details/`
- `data/applications/`，只有加 `--download-applications` 时生成

CSV 中包含项目编号、项目名称、社区、难度、技术标签、项目简介、产出要求和仓库链接等字段。
