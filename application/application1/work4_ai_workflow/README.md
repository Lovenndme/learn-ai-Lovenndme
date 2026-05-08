# 作业 4：凯瑟琳不想发委托

## 任务目标

构建一个至少包含 3 个节点的 AI 工作流，将一封啰嗦、带有情绪表达的求助信转换成标准委托广告。

本实现的 pipeline：

1. 信息净化与提取：删除抱怨、寒暄和情绪表达，只保留客观事实。
2. 结构化处理：把客观事实转换成 JSON。
3. 文案包装：把结构化 JSON 改写为冒险家协会招募广告。

## 运行方式

先设置智谱 API Key：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

运行真实 GLM 工作流：

```bash
cd application/application1
python3 work4_ai_workflow/commission_workflow.py --save-output
```

没有 API Key 时可以运行 mock：

```bash
python3 work4_ai_workflow/commission_workflow.py --mock --save-output
```

## 错误处理

节点 2 会把模型输出交给 `json.loads` 解析，并校验字段结构：

- `client`：字符串
- `location`：字符串
- `tasks`：非空字符串数组
- `reward`：字符串
- `deadline`：字符串

如果模型输出不是合法 JSON，或字段不符合要求，程序会把错误内容和 schema 要求重新交给 GLM，让它只输出修复后的合法 JSON。

## 输出文件

运行结果保存到：

- `output/commission_workflow_result.json`

文件中包含：

- 原始求助信
- 节点 1 的净化文本
- 节点 2 的结构化 JSON
- 节点 3 的招募广告

## 真实运行记录

节点 1：信息净化

```text
委托人普通商人，地点城外旧商路断桥附近，任务今晚巡查确认是否有怪物并将倒在路中央的木箱搬到路边，时间限制今晚，报酬800摩拉和一箱苹果。
```

节点 2：结构化 JSON

```json
{
  "client": "普通商人",
  "location": "城外旧商路断桥附近",
  "tasks": [
    "今晚巡查确认是否有怪物",
    "将倒在路中央的木箱搬到路边"
  ],
  "reward": "800摩拉和一箱苹果",
  "deadline": "今晚"
}
```

节点 3：招募广告

```text
【冒险家协会招募】

委托人：普通商人
地点：城外旧商路断桥附近
任务内容：
1. 今晚巡查该区域，确认是否有怪物出没；
2. 将倒在路中央的木箱搬运至路边。
截止时间：今晚
报酬：800摩拉及一箱苹果

符合条件者请即刻接取委托。
```

## 小结

这个脚本把 AI 调用拆成了三个职责清晰的节点，而不是把所有逻辑写在主函数里。节点 2 的 JSON 校验和修复逻辑保证了后续节点能拿到结构化数据，也展示了 AI 工作流中常见的“模型输出 + 程序校验 + 失败修复”的处理方式。
