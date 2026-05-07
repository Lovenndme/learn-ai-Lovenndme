# Task 2 作业 2：使用 Selenium 爬取知乎话题

本作业使用 Selenium 打开浏览器，爬取知乎话题：

```text
https://www.zhihu.com/topic/19554298/top-answers
```

目标是爬取 20 个问题，每个问题最多爬取 10 条回答，并保存成 CSV。

## 输出内容

脚本会生成：

```text
data/zhihu_topic_answers.csv
```

CSV 字段如下：

- `question_index`：第几个问题
- `question_title`：问题名
- `question_detail`：问题具体内容
- `question_url`：问题链接
- `answer_index`：该问题下第几条回答
- `answer_author`：回答作者
- `answer_text`：回答纯文字
- `answer_url`：回答链接

## 安装依赖

进入本目录：

```bash
cd foundation/task2/work2_zhihu_selenium_crawler
```

安装 Selenium：

```bash
python3 -m pip install -r requirements.txt
```

Selenium 4 会尝试自动管理浏览器驱动。建议本机已经安装 Chrome；如果你想用 Edge，可以运行时加 `--browser edge`。

## 运行方式

第一次运行建议用普通浏览器模式：

```bash
python3 crawler.py
```

运行后会打开浏览器。如果知乎要求登录，就在浏览器里扫码或输入账号正常登录；看到话题内容后，回到终端按 Enter，脚本会继续自动滚动和采集。

默认会爬：

- 20 个问题
- 每个问题最多 10 条回答

少量测试可以这样运行：

```bash
python3 crawler.py --question-limit 2 --answer-limit 2
```

如果已经登录过，并且想复用登录状态：

```bash
python3 crawler.py --skip-login-prompt
```

## 常用参数

- `--question-limit 20`：最多爬取多少个问题
- `--answer-limit 10`：每个问题最多爬取多少条回答
- `--delay 1.5`：滚动之间等待多久，网络慢可以调大
- `--browser chrome`：使用 Chrome
- `--browser edge`：使用 Edge
- `--profile-dir data/browser_profile`：指定浏览器登录状态保存目录

## 注意

本脚本不绕过知乎登录、验证码或权限限制。知乎如果弹出登录页，直接按页面要求正常登录即可。
