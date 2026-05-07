# Task 2 作业 1 - 福大教务通知爬虫

本作业用于爬取福州大学教务处“教学通知”栏目。

目标页面：

<https://jwch.fzu.edu.cn/jxtz.htm>

## 爬取内容

- 通知人 / 发布部门
- 通知标题
- 发布日期
- 详情页链接
- 详情页 HTML，本地保存
- 详情页正文文本
- 附件名称
- 附件下载链接
- 附件 file id
- 通过 Ajax 接口获取的附件下载次数

脚本会生成两个 CSV 文件：

- `data/notices.csv`：每行对应一条通知
- `data/attachments.csv`：每行对应一个附件

生成的数据已加入 `.gitignore`，不会直接提交到 Git 仓库。如果需要查看 CSV，可以在本地运行脚本重新生成。

初始实现由 Codex 辅助完成；提交前需要确保自己理解代码每一部分的作用。

## 运行方式

```bash
python3 crawler.py --limit 500
```

快速测试：

```bash
python3 crawler.py --limit 5 --delay 0
```

如果还想把附件文件下载到本地：

```bash
python3 crawler.py --limit 500 --download-attachments
```

## 说明

附件下载次数是在页面中动态加载的。脚本调用了页面实际使用的接口：

```text
/system/resource/code/news/click/clicktimes.jsp
```

因此不需要使用 Selenium 也可以获取附件下载次数。
