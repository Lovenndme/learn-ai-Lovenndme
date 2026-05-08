# 作业 4：凯瑟琳不想发委托

## 我做了什么

这题是把一封啰嗦的求助信整理成委托广告。我没有直接让模型一步写完，而是拆成了三步：

1. 先把原文里的抱怨和寒暄删掉，只留事实。
2. 再把事实整理成 JSON。
3. 最后根据 JSON 写成冒险家协会的招募广告。

## 运行方式

先设置 API Key：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

运行：

```bash
cd application/application1
python3 work4_ai_workflow/commission_workflow.py --save-output
```

没有 API Key 时可以先跑 mock：

```bash
python3 work4_ai_workflow/commission_workflow.py --mock --save-output
```

## 错误处理

节点 2 是这个脚本里最容易出问题的一步，所以我加了字段校验。模型输出会先交给 `json.loads` 解析，再检查这些字段：

- `client`：字符串
- `location`：字符串
- `tasks`：非空字符串数组
- `reward`：字符串
- `deadline`：字符串

如果模型输出不是合法 JSON，或者字段缺了、类型不对，程序会把错误内容和字段要求重新发给 GLM，让它再修一次。

## 输出文件

结果保存在：

- `output/commission_workflow_result.json`

里面包含：

- 原始求助信
- 节点 1 的净化文本
- 节点 2 的结构化 JSON
- 节点 3 的招募广告

## 运行结果

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

拆成三步之后，流程比直接一口气生成广告更好控制。尤其是中间有 JSON 这一层，后面要改广告格式或者接别的程序会方便一些。节点 2 的校验和修复主要是防止模型偶尔输出不合法 JSON。
