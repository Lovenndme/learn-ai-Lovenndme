# 作业 3：星临者情报终端

## 任务目标

调用智谱 GLM 生成和解析 JSON，并确保输出能被 Python 的 `json` 模块正确解析。本实现覆盖：

- 基础 JSON 生成：角色姓名、等级、所属势力
- 进阶 JSON 生成：数组、嵌套对象、布尔值和坐标
- 大型 JSON 分块生成：10 个角色，每个角色 100 只奇波
- JSONL 导出：大型数据按行保存
- 火属性奇波坐标提取：本地代码提取 + AI 分块提取
- 错误处理：代码校验 + 将错误 JSON 重新交给 AI 修复

## 运行方式

先设置智谱 API Key：

```bash
export ZHIPUAI_API_KEY="你的 API Key"
export GLM_MODEL="glm-5.1"
```

运行真实 GLM 调用：

```bash
cd application/application1
python3 work3_json_glm/json_tasks.py
```

没有 API Key 时可以先跑 mock：

```bash
python3 work3_json_glm/json_tasks.py --mock
```

如果网络较慢，可以调大超时时间或重试次数：

```bash
GLM_TIMEOUT=180 GLM_RETRIES=4 python3 work3_json_glm/json_tasks.py
```

## 分块策略

大型 JSON 不一次性让模型生成完整对象，而是拆成较小任务：

1. 每个角色需要 100 只奇波。
2. 程序把 100 只奇波拆成 4 批，每批 25 个对象。
3. 每批由 GLM 输出一个 JSON 数组。
4. 程序校验每批数组长度、字段和类型。
5. 最后由代码拼装为一个角色对象，并写入 `characters.jsonl`。

这种方式可以避免单次响应过长导致超时，也更接近真实业务里的分块/流式处理思路。

## 错误处理

程序包含两层错误处理：

1. 代码校验：检查 JSON 是否能被 `json.loads` 解析，并验证字段类型、数组长度、坐标格式和枚举值。
2. AI 修复：如果 JSON 解析失败或结构校验失败，程序会把错误内容、错误信息和 schema 要求重新发给 GLM，让它只输出修复后的合法 JSON。

## 输出文件

运行后会在 `output/` 下生成：

- `simple_character.json`：基础角色 JSON
- `nested_character.json`：复杂嵌套角色 JSON
- `characters.jsonl`：10 个角色的大型 JSONL 数据
- `fire_kibot_coordinates.jsonl`：本地代码提取出的火属性奇波坐标
- `fire_kibot_coordinates_ai.jsonl`：GLM 分块提取出的火属性奇波坐标

## 真实运行记录

- 模型：`glm-5.1`
- 大型生成方式：每 25 只奇波一批
- 角色数量：10
- 每个角色奇波数量：100
- `characters.jsonl` 行数：10
- 本地代码提取火属性奇波坐标数量：362
- AI 分块提取火属性奇波坐标数量：362

示例输出：

```text
基础 JSON： {'name': '艾瑞克', 'level': 42, 'faction': '银色黎明'}
复杂 JSON： {'name': '艾莉丝·星陨', 'element': '虚空', ...}
角色数量：10
火属性奇波坐标数量（代码提取）：362
火属性奇波坐标数量（AI 提取）：362
```

## 小结

本次作业展示了如何用 GLM 生成严格 JSON、如何对模型输出进行本地校验、如何在格式错误时让 AI 参与修复，以及如何把大型 JSON 任务拆成多个小块处理。最终代码提取和 AI 提取的火属性奇波坐标数量一致，说明分块解析流程能够稳定完成目标任务。
