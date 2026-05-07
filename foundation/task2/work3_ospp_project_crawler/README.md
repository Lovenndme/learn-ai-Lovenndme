# Task 2 作业 3：开源之夏项目接口爬虫

这个脚本爬取开源之夏官网的公开项目数据，数据来源是页面实际调用的公开接口：

- 项目列表接口：`https://summer-ospp.ac.cn/api/getProList`
- 项目详情接口：`https://summer-ospp.ac.cn/api/getProDetail`
- 项目申请书接口：`https://summer-ospp.ac.cn/api/publicApplication`

## 能完成什么

脚本会先调用项目列表接口，拿到每个项目的项目编号、项目名称、社区、难度、技术标签等信息；再根据项目编号请求详情接口，补充项目简介、产出要求、技术要求、项目仓库、导师邮箱等字段。

默认输出：

- `data/projects.csv`：整理后的项目表格
- `data/projects.json`：整理后的 JSON 数据
- `data/raw_details/*.json`：每个项目的原始列表数据和详情数据

如果加上 `--download-applications`，还会把中选项目申请书 PDF 下载到：

- `data/applications/*.pdf`

## 运行方式

先进入本目录：

```bash
cd foundation/task2/work3_ospp_project_crawler
```

抓取前 20 个项目：

```bash
python3 crawler.py --limit 20
```

抓取前 5 个项目，并下载项目申请书 PDF：

```bash
python3 crawler.py --limit 5 --download-applications
```

抓取全部项目：

```bash
python3 crawler.py --limit 0
```

按项目名称关键词搜索：

```bash
python3 crawler.py --keyword RISC-V --limit 20
```

## CSV 字段说明

- `program_code`：项目编号
- `project_name`：项目名称
- `org_name`：社区名称
- `difficulty`：项目难度
- `support_language`：项目支持语言
- `selected_student`：中选学生
- `tech_tags`：技术标签
- `programming_language_tags`：编程语言标签
- `description`：项目简介
- `output_requirements`：产出要求
- `tech_requirements`：技术要求
- `repos`：项目相关仓库
- `mentor_name`、`mentor_email`：导师信息
- `completion_time_hours`、`arch`：预期完成时间和支持架构
- `license`：开源许可证
- `detail_url`：项目详情页
- `application_pdf_url`：申请书预览页
- `application_pdf_file`：本地申请书 PDF 路径
- `raw_detail_file`：原始详情 JSON 路径

## 注意

这个脚本只访问开源之夏官网公开接口，不需要登录，也不会访问任何学校内部系统。
