# Application 1 简单 AI 应用

## 文件

- `work1_model_test/report.md`：模型能力测试记录
- `work2_sentiment_glm/sentiment_demo.py`：调用 GLM 做情绪分类
- `work2_sentiment_glm/README.md`：情绪分类提示词设计和运行记录
- `work3_json_glm/json_tasks.py`：JSON 生成、解析和校验
- `work3_json_glm/README.md`：JSON 分块生成、错误处理和运行记录
- `work4_ai_workflow/commission_workflow.py`：三节点 AI 工作流
- `work4_ai_workflow/README.md`：AI 工作流设计和运行记录
- `common/glm_client.py`：GLM API 简单封装

## 准备

需要在智谱开放平台申请 API Key，然后在终端设置环境变量：

```bash
export ZHIPUAI_API_KEY="你的 key"
```

不要把 API Key 写进代码，也不要提交 `.env` 文件。

## 运行

```bash
cd application/application1
python3 work2_sentiment_glm/sentiment_demo.py
python3 work3_json_glm/json_tasks.py
python3 work4_ai_workflow/commission_workflow.py
```

如果还没申请 key，可以先加 `--mock` 看脚本流程：

```bash
python3 work2_sentiment_glm/sentiment_demo.py --mock
python3 work3_json_glm/json_tasks.py --mock
python3 work4_ai_workflow/commission_workflow.py --mock
```
