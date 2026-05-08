# 作业 2：橘雪莉妙妙屋

## 任务目标

调用智谱 GLM API，对群友消息、表情包或图片进行情绪分析。程序需要输出一个预先定义好的心情标签，并根据标签从对应表情包列表中随机选择一个回应。

本实现使用的情绪标签为：

- 开心
- 难过
- 愤怒
- 中性

## 提示词设计

文本分析使用 `glm-5.1`，图片分析直接使用具备视觉能力的 `glm-5v-turbo`。两种模式都会把 GLM 约束为情绪分类器，并明确要求：

1. 只能从 `开心、难过、愤怒、中性` 中选择一个标签。
2. 不要解释。
3. 不要输出标点。
4. 不要输出其他文字。

如果模型输出中混入了标点或其他短文本，程序会通过 `normalize_label` 做一次简单归一化；如果仍无法匹配，则回退为 `中性`，避免程序崩溃。

## 运行方式

先在终端设置环境变量：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

再运行：

```bash
cd application/application1
python3 work2_sentiment_glm/sentiment_demo.py
```

如果需要保存运行结果：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --save-output
```

也可以分析单句：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --text "今天终于把作业跑通了！"
```

分析图片或表情包时，直接传入本地图片路径或图片 URL：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image path/to/meme.png
python3 work2_sentiment_glm/sentiment_demo.py --image "https://example.com/meme.png"
```

图片分析结果也可以保存：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image path/to/meme.png --save-output
```

批量分析目录下的图片：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image-dir work2_sentiment_glm/input_images --save-output
```

没有 API Key 时，可以使用 mock 模式查看流程：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --mock
```

保存后的文件位于 `work2_sentiment_glm/output/`：

- `text_sentiment_results.json`
- `image_sentiment_result.json`
- `image_sentiment_results.json`
- `input_images/`：图片情绪分析测试素材

## 真实运行记录

### 文本情绪分析

- 模型：`glm-5.1`
- 方式：真实 GLM API 调用

```text
详见 output/text_sentiment_results.json
```

### 图片情绪分析

- 模型：`glm-5v-turbo`
- 方式：直接把图片输入视觉模型，由模型输出限定情绪标签

```bash
python3 work2_sentiment_glm/sentiment_demo.py --image path/to/meme.png
```

示例输出：

```text
图片：work2_sentiment_glm/output/sample_register.png
情绪：中性
表情包：normal_02.png
```

批量图片测试使用 `input_images/` 下的无文字标签图片，结果会保存到 `output/image_sentiment_results.json`。

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

本次测试中，文本 GLM 能够按照提示词输出限定标签，没有输出额外解释文本。四条测试消息分别覆盖了开心、难过、愤怒和中性四类情绪，分类结果与人工判断基本一致。图片模式则直接调用视觉 GLM 分析图片或表情包表达出的情绪，并复用同一套标签和表情包选择逻辑。随后程序根据标签随机选择了对应类别的表情包文件名，完成了从消息/图片分析到表情包回应的基本流程。
