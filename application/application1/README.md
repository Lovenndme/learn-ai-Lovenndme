# Application 1 简单 AI 应用

## 目录

- `work1_model_test/`：DeepSeek 测试记录和观察
- `work2_sentiment_glm/`：用 GLM 做文本/图片情绪分类
- `work3_json_glm/`：让 GLM 生成、修复和解析 JSON
- `work4_ai_workflow/`：把求助信整理成委托广告的三步工作流
- `common/glm_client.py`：几个作业共用的 GLM 请求封装

## 准备

代码里没有写 API Key。运行前需要自己在终端里设置：

```bash
export ZHIPUAI_API_KEY="你的 key"
```

也可以用 `GLM_MODEL` 指定模型，例如：

```bash
export GLM_MODEL="glm-5.1"
```

## 运行

```bash
cd application/application1
python3 work2_sentiment_glm/sentiment_demo.py
python3 work3_json_glm/json_tasks.py
python3 work4_ai_workflow/commission_workflow.py
```

没有 key 或者只是想看流程，可以先跑 mock：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --mock
python3 work3_json_glm/json_tasks.py --mock
python3 work4_ai_workflow/commission_workflow.py --mock
```
