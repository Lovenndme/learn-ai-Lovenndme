# Task2 作业1：福大教务通知

爬取福州大学教务处教学通知：<https://jwch.fzu.edu.cn/jxtz.htm>

## 运行

```bash
python3 crawler.py --limit 500
```

测试少量数据：

```bash
python3 crawler.py --limit 5 --delay 0
```

下载附件：

```bash
python3 crawler.py --limit 500 --download-attachments
```

## 输出

- `data/notices.csv`：通知列表
- `data/attachments.csv`：附件列表
- `data/details/`：通知详情 HTML

附件下载次数通过页面的 Ajax 接口获取，不使用 Selenium。
