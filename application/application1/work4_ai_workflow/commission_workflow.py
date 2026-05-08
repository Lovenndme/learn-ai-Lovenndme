from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.glm_client import GlmError, chat


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
RAW_LETTER = """
凯瑟琳小姐你好，我真的受不了了。最近城外那条旧商路每天晚上都传来奇怪的响声，
大家都说可能是史莱姆，也有人说是风吹倒了破木牌。可是我家的货车明天必须从那里经过，
如果路上有危险，货物肯定会损坏。我只是一个普通商人，真的没有办法自己去确认。
希望冒险家协会可以派人今晚去旧商路巡查一下，重点看看断桥附近有没有怪物，
如果可以的话，顺便把倒在路中央的木箱搬到路边。报酬我可以给 800 摩拉和一箱苹果。
"""


def mock_clean_text(_: str) -> str:
    return (
        "委托人是一名商人。旧商路夜间出现异常响声，疑似有怪物或路障。"
        "商人的货车明天需要经过该路段。需要冒险家今晚巡查旧商路，"
        "重点检查断桥附近，并清理路中央木箱。报酬为 800 摩拉和一箱苹果。"
    )


def mock_extract_json(_: str) -> dict:
    return {
        "client": "商人",
        "location": "城外旧商路断桥附近",
        "tasks": ["夜间巡查", "确认是否有怪物", "清理路中央木箱"],
        "reward": "800 摩拉和一箱苹果",
        "deadline": "今晚",
    }


def mock_write_ad(data: dict) -> str:
    tasks = "、".join(data["tasks"])
    return (
        f"冒险家协会委托：请前往{data['location']}完成{tasks}。"
        f"委托需在{data['deadline']}完成，报酬为{data['reward']}。"
    )


def validate_task_data(data: Any) -> dict:
    if not isinstance(data, dict):
        raise ValueError("结构化结果必须是 JSON 对象")

    required_string_fields = ["client", "location", "reward", "deadline"]
    for field in required_string_fields:
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"{field} 必须是非空字符串")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks 必须是非空数组")
    if not all(isinstance(task, str) and task.strip() for task in tasks):
        raise ValueError("tasks 中每一项都必须是非空字符串")

    return data


def parse_or_repair_json(output: str) -> dict:
    try:
        return validate_task_data(json.loads(output))
    except (json.JSONDecodeError, ValueError) as first_error:
        repair_prompt = (
            "下面这段文本本来应该是委托信息 JSON，但格式或字段不符合要求。"
            "请只输出修复后的合法 JSON，不要解释。\n\n"
            "字段要求：client(str)、location(str)、tasks(str[])、reward(str)、deadline(str)。\n"
            f"错误信息：{first_error}\n"
            f"待修复内容：\n{output}"
        )
        fixed = chat(
            [
                {"role": "system", "content": "你只输出可以被 json.loads 解析的合法 JSON。"},
                {"role": "user", "content": repair_prompt},
            ],
            temperature=0.01,
        )
        try:
            return validate_task_data(json.loads(fixed))
        except (json.JSONDecodeError, ValueError) as second_error:
            raise ValueError(f"JSON 修复失败：{first_error}; 修复后仍失败：{second_error}") from second_error


def clean_text(raw_text: str, mock: bool) -> str:
    if mock:
        return mock_clean_text(raw_text)
    return chat(
        [
            {
                "role": "system",
                "content": (
                    "你负责从委托信中提取客观事实，删除抱怨、情绪化表达和无关寒暄。"
                    "保留委托人、地点、任务、报酬、时间限制等关键信息。"
                    "只输出一段纯文本，不要使用 Markdown、编号列表或加粗。"
                ),
            },
            {"role": "user", "content": raw_text},
        ],
        temperature=0.1,
    )


def extract_json(cleaned_text: str, mock: bool) -> dict:
    if mock:
        return mock_extract_json(cleaned_text)

    prompt = (
        "请把下面的客观事实整理成合法 JSON。字段包含 client、location、tasks、reward、deadline。"
        "client、location、reward、deadline 是字符串；tasks 是字符串数组。"
        "只输出 JSON，不要解释，不要 Markdown。\n\n"
        f"{cleaned_text}"
    )
    output = chat(
        [
            {"role": "system", "content": "你只输出可以被 json.loads 解析的 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.01,
    )
    return parse_or_repair_json(output)


def write_ad(task_data: dict, mock: bool) -> str:
    if mock:
        return mock_write_ad(task_data)
    return chat(
        [
            {
                "role": "system",
                "content": (
                    "你负责把结构化委托信息改写为简洁的冒险家协会招募广告。"
                    "语气正式清楚，包含地点、任务、截止时间和报酬，不要编造新事实。"
                ),
            },
            {"role": "user", "content": json.dumps(task_data, ensure_ascii=False)},
        ],
        temperature=0.4,
    )


def run_workflow(raw_text: str, mock: bool) -> tuple[str, dict, str]:
    cleaned = clean_text(raw_text, mock)
    task_data = extract_json(cleaned, mock)
    ad = write_ad(task_data, mock)
    return cleaned, task_data, ad


def save_workflow_result(raw_text: str, cleaned: str, task_data: dict, ad: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "commission_workflow_result.json"
    payload = {
        "raw_letter": raw_text.strip(),
        "node_1_cleaned_text": cleaned,
        "node_2_structured_json": task_data,
        "node_3_advertisement": ad,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-output", action="store_true", help="把工作流结果保存到 output 目录")
    parser.add_argument("--mock", action="store_true", help="不调用 API，只演示流程")
    args = parser.parse_args()

    try:
        cleaned, task_data, ad = run_workflow(RAW_LETTER, args.mock)
    except (GlmError, ValueError) as error:
        print(error)
        print("可以先使用 --mock 查看流程。")
        return

    print("节点 1：信息净化")
    print(cleaned)
    print("\n节点 2：结构化 JSON")
    print(json.dumps(task_data, ensure_ascii=False, indent=2))
    print("\n节点 3：招募广告")
    print(ad)

    if args.save_output:
        path = save_workflow_result(RAW_LETTER, cleaned, task_data, ad)
        print(f"\n结果文件：{path}")


if __name__ == "__main__":
    main()
