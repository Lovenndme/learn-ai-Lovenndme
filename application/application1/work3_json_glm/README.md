# 作业 3：星临者情报终端

## 我做了什么

这个作业主要是试一下：让 GLM 输出 JSON 时，怎样让它尽量稳定、能被代码直接读进去。

我写了几部分：

- 基础 JSON 生成：角色姓名、等级、所属势力
- 进阶 JSON 生成：数组、嵌套对象、布尔值和坐标
- 大型 JSON 分块生成：10 个角色，每个角色 100 只奇波
- JSONL 导出：大型数据按行保存
- 火属性奇波坐标提取：本地代码提取 + AI 分块提取
- 错误处理：先用代码校验，出错时再把错误内容交给 GLM 修复

## 运行方式

先设置 API Key：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

运行：

```bash
cd application/application1
python3 work3_json_glm/json_tasks.py
```

没有 API Key 时先跑 mock：

```bash
python3 work3_json_glm/json_tasks.py --mock
```

这部分 API 调用次数比较多，网络慢的话可以加大超时和重试：

```bash
GLM_TIMEOUT=180 GLM_RETRIES=4 python3 work3_json_glm/json_tasks.py
```

## 分块策略

一开始我尝试让模型一次生成比较大的 JSON，容易慢或者超时，所以最后改成了更小的块：

1. 每个角色需要 100 只奇波。
2. 程序把 100 只奇波拆成 4 批，每批 25 个对象。
3. 每批由 GLM 输出一个 JSON 数组。
4. 程序校验每批数组长度、字段和类型。
5. 最后由代码拼装为一个角色对象，并写入 `characters.jsonl`。

这样单次输出短一些，也方便每一块都做校验。

## 错误处理

这里没有完全相信模型输出，而是做了两层处理：

1. 代码校验：检查 JSON 是否能被 `json.loads` 解析，并验证字段类型、数组长度、坐标格式和枚举值。
2. AI 修复：如果 JSON 解析失败或结构校验失败，就把错误内容、错误信息和字段要求重新发给 GLM，让它修成合法 JSON。

## 输出文件

`output/` 里保留了这几份结果：

- `simple_character.json`：基础角色 JSON
- `nested_character.json`：复杂嵌套角色 JSON
- `characters.jsonl`：10 个角色的大型 JSONL 数据
- `fire_kibot_coordinates.jsonl`：本地代码提取出的火属性奇波坐标
- `fire_kibot_coordinates_ai.jsonl`：GLM 分块提取出的火属性奇波坐标

## 运行结果

- 模型：`glm-5.1`
- 大型生成方式：每 25 只奇波一批
- 角色数量：10
- 每个角色奇波数量：100
- `characters.jsonl` 行数：10
- 本地代码提取火属性奇波坐标数量：362
- AI 分块提取火属性奇波坐标数量：362

终端里最后的统计是：

```text
基础 JSON： {'name': '艾瑞克', 'level': 42, 'faction': '银色黎明'}
复杂 JSON： {'name': '艾莉丝·星陨', 'element': '虚空', ...}
角色数量：10
火属性奇波坐标数量（代码提取）：362
火属性奇波坐标数量（AI 提取）：362
```

## 小结

这一题做完之后，感觉关键不是“让模型随便吐一段 JSON”，而是要给它足够明确的字段要求，然后用程序兜底校验。最后本地代码提取和 GLM 分块提取都得到 362 条火属性奇波坐标，说明这个流程至少在这组数据上是对得上的。
