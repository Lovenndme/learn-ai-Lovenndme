# Task2 作业2：知乎话题

使用 Selenium 爬取知乎话题页：

```text
https://www.zhihu.com/topic/19554298/top-answers
```

爬 20 个问题，每个问题最多 10 条回答。

## 安装

```bash
python3 -m pip install -r requirements.txt
```

## 运行

```bash
python3 crawler.py
```

浏览器打开后，如果知乎要求登录，先正常登录。能看到话题内容后，回到终端按 Enter。

少量测试：

```bash
python3 crawler.py --question-limit 2 --answer-limit 2 --delay 8
```

## 输出

- `data/zhihu_topic_answers.csv`

字段包括问题标题、问题描述、问题链接、回答作者、回答内容和回答链接。

知乎可能会出现 `40362` 临时限制，这时先停一会儿再跑。
