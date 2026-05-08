# 作业 2：橘雪莉妙妙屋

## 我做了什么

这个小作业是用 GLM 判断消息或者图片里的情绪，然后按情绪挑一个表情包文件名。

我先用了四个比较容易区分的标签：

- 开心
- 难过
- 愤怒
- 中性

标签当然可以继续加，比如焦虑、惊讶、困惑之类。这里先保持简单，是为了让模型输出更稳定一点。

## 提示词

文本用 `glm-5.1`，图片用 `glm-5v-turbo`。提示词里主要强调一件事：只能输出我给定的标签，不能解释，也不要带标点。

实际跑的时候模型基本能按要求输出。为了稳一点，我在代码里也做了 `normalize_label`，如果模型多输出了句号或者一小段文字，就尽量把里面的标签取出来；如果实在匹配不上，就先当成中性。

## 运行方式

先设置环境变量：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

默认会跑几条文本样例：

```bash
cd application/application1
python3 work2_sentiment_glm/sentiment_demo.py
```

保存结果：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --save-output
```

分析单句：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --text "今天终于把作业跑通了！"
```

分析图片或表情包：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image path/to/meme.png
python3 work2_sentiment_glm/sentiment_demo.py --image "https://example.com/meme.png"
```

图片结果也可以保存：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image path/to/meme.png --save-output
```

批量分析一个目录里的图片：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image-dir work2_sentiment_glm/input_images --save-output
```

没有 API Key 时，可以先看 mock 流程：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --mock
```

我保留的结果文件：

- `text_sentiment_results.json`
- `image_sentiment_results.json`
- `input_images/`：图片情绪分析测试素材

## 运行结果

### 文本情绪分析

文本结果在 `output/text_sentiment_results.json` 里，四条样例分别覆盖了开心、难过、愤怒和中性。

```text
详见 output/text_sentiment_results.json
```

### 图片情绪分析

图片我用了 `input_images/` 下面的几张无文字提示图片，避免把答案直接写在图上。批量结果保存在 `output/image_sentiment_results.json`。

本次测试图片结果：

```text
图片：work2_sentiment_glm/input_images/angry.png
情绪：愤怒
表情包：angry_01.png

图片：work2_sentiment_glm/input_images/happy.png
情绪：开心
表情包：happy_02.png

图片：work2_sentiment_glm/input_images/sad_1.png
情绪：难过
表情包：sad_01.png

图片：work2_sentiment_glm/input_images/sad_2.png
情绪：难过
表情包：sad_01.png
```

## 小结

这部分主要是熟悉 GLM API 的基本调用。文本和图片都能归到同一套情绪标签里，后面只要换成真实表情包文件，就可以接到“按情绪回复表情包”的流程上。
