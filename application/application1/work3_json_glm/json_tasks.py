from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.glm_client import GlmError, chat


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
ELEMENTS = ["火", "水", "风", "雷", "土"]
STATUSES = ["active", "resting", "lost"]
KIBOTS_PER_CHARACTER = 100
KIBOT_BATCH_SIZE = 25


JsonValue = dict[str, Any] | list[Any]
Validator = Callable[[JsonValue], None]


def ask_json(
    prompt: str,
    mock_data: JsonValue,
    mock: bool = False,
    *,
    schema_hint: str = "",
    validator: Validator | None = None,
) -> JsonValue:
    if mock:
        if validator:
            validator(mock_data)
        return mock_data

    messages = [
        {
            "role": "system",
            "content": (
                "你只输出合法 JSON，不要输出 Markdown，不要解释。"
                "JSON 必须能被 Python json.loads 直接解析。"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    output = chat(messages, temperature=0.01)
    return parse_or_repair(output, schema_hint=schema_hint, validator=validator)


def parse_or_repair(
    text: str,
    *,
    schema_hint: str = "",
    validator: Validator | None = None,
) -> JsonValue:
    current = text
    last_error: Exception | None = None

    for _ in range(3):
        try:
            data = json.loads(current)
            if validator:
                validator(data)
            return data
        except (json.JSONDecodeError, ValueError) as error:
            last_error = error
            current = repair_json_with_ai(current, str(error), schema_hint)

    raise ValueError(f"JSON 解析或校验失败：{last_error}")


def repair_json_with_ai(text: str, error: str, schema_hint: str) -> str:
    repair_prompt = (
        "下面这段文本本来应该是 JSON，但解析或结构校验失败。"
        "请只输出修正后的合法 JSON，不要解释。\n\n"
        f"校验要求：{schema_hint or '保持原意，输出合法 JSON。'}\n"
        f"错误信息：{error}\n\n"
        f"待修复内容：\n{text}"
    )
    return chat(
        [
            {"role": "system", "content": "你只输出合法 JSON，不要输出 Markdown。"},
            {"role": "user", "content": repair_prompt},
        ],
        temperature=0.01,
    )


def require_dict(data: JsonValue, name: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{name} 必须是 JSON 对象")
    return data


def require_list(data: JsonValue, name: str) -> list[Any]:
    if not isinstance(data, list):
        raise ValueError(f"{name} 必须是 JSON 数组")
    return data


def require_coordinates(value: Any, name: str) -> None:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} 必须是长度为 2 的坐标数组")
    if not all(isinstance(item, int | float) for item in value):
        raise ValueError(f"{name} 的坐标值必须是数字")


def validate_simple_character(data: JsonValue) -> None:
    character = require_dict(data, "基础角色")
    if not isinstance(character.get("name"), str):
        raise ValueError("name 必须是字符串")
    if not isinstance(character.get("level"), int):
        raise ValueError("level 必须是整数")
    if not isinstance(character.get("faction"), str):
        raise ValueError("faction 必须是字符串")


def validate_nested_character(data: JsonValue) -> None:
    character = require_dict(data, "复杂角色")
    if not isinstance(character.get("name"), str):
        raise ValueError("name 必须是字符串")
    if not isinstance(character.get("element"), str):
        raise ValueError("element 必须是字符串")
    hobbies = character.get("hobbies")
    if not isinstance(hobbies, list) or not all(isinstance(item, str) for item in hobbies):
        raise ValueError("hobbies 必须是字符串数组")
    partner = character.get("kibot_partner")
    if not isinstance(partner, dict):
        raise ValueError("kibot_partner 必须是对象")
    for key in ["species", "color"]:
        if not isinstance(partner.get(key), str):
            raise ValueError(f"kibot_partner.{key} 必须是字符串")
    if not isinstance(partner.get("bond_level"), int):
        raise ValueError("kibot_partner.bond_level 必须是整数")
    require_coordinates(partner.get("coordinates"), "kibot_partner.coordinates")
    if not isinstance(partner.get("is_friendly"), bool):
        raise ValueError("kibot_partner.is_friendly 必须是布尔值")


def validate_character_chunk(data: JsonValue) -> None:
    character = require_dict(data, "角色块")
    if not isinstance(character.get("name"), str):
        raise ValueError("name 必须是字符串")
    kibots = character.get("kibots")
    if not isinstance(kibots, list) or len(kibots) != KIBOTS_PER_CHARACTER:
        raise ValueError(f"kibots 必须是长度为 {KIBOTS_PER_CHARACTER} 的数组")
    validate_kibot_items(kibots)


def validate_kibot_batch(data: JsonValue, expected_count: int) -> None:
    kibots = require_list(data, "奇波分块")
    if len(kibots) != expected_count:
        raise ValueError(f"奇波分块必须包含 {expected_count} 个对象")
    validate_kibot_items(kibots)


def validate_kibot_items(kibots: list[Any]) -> None:
    for index, kibot in enumerate(kibots, start=1):
        if not isinstance(kibot, dict):
            raise ValueError(f"第 {index} 个 kibot 必须是对象")
        if not isinstance(kibot.get("id"), str):
            raise ValueError(f"第 {index} 个 kibot.id 必须是字符串")
        if kibot.get("element") not in ELEMENTS:
            raise ValueError(f"第 {index} 个 kibot.element 必须属于 {ELEMENTS}")
        if kibot.get("status") not in STATUSES:
            raise ValueError(f"第 {index} 个 kibot.status 必须属于 {STATUSES}")
        require_coordinates(kibot.get("coordinates"), f"第 {index} 个 kibot.coordinates")


def validate_fire_points(data: JsonValue) -> None:
    rows = require_list(data, "火属性奇波坐标列表")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"第 {index} 条结果必须是对象")
        if not isinstance(row.get("owner"), str):
            raise ValueError(f"第 {index} 条 owner 必须是字符串")
        if not isinstance(row.get("id"), str):
            raise ValueError(f"第 {index} 条 id 必须是字符串")
        require_coordinates(row.get("coordinates"), f"第 {index} 条 coordinates")


def simple_generation(mock: bool) -> dict:
    prompt = (
        "生成一个角色 JSON，字段只能包含 name、level、faction。"
        "name 是字符串，level 是整数，faction 是字符串。"
    )
    mock_data = {"name": "洛卿", "level": 20, "faction": "云海遥"}
    data = ask_json(
        prompt,
        mock_data,
        mock,
        schema_hint="对象字段只能包含 name(str)、level(int)、faction(str)。",
        validator=validate_simple_character,
    )
    assert isinstance(data, dict)
    return data


def nested_generation(mock: bool) -> dict:
    prompt = (
        "生成一个复杂角色 JSON，字段包含 name、element、hobbies、kibot_partner。"
        "hobbies 是字符串数组；kibot_partner 是对象，包含 species、color、bond_level、"
        "coordinates、is_friendly。"
    )
    mock_data = {
        "name": "寒悠悠",
        "element": "火",
        "hobbies": ["武艺", "机关", "烟花"],
        "kibot_partner": {
            "species": "菜鸡",
            "color": "金",
            "bond_level": 5,
            "coordinates": [123.45, 67.89],
            "is_friendly": True,
        },
    }
    data = ask_json(
        prompt,
        mock_data,
        mock,
        schema_hint=(
            "对象字段包含 name(str)、element(str)、hobbies(str[])、"
            "kibot_partner(object)。kibot_partner 包含 species(str)、color(str)、"
            "bond_level(int)、coordinates(number[2])、is_friendly(bool)。"
        ),
        validator=validate_nested_character,
    )
    assert isinstance(data, dict)
    return data


def chunked_generation(mock: bool) -> list[dict]:
    characters: list[dict] = []
    for index in range(10):
        if mock:
            character = {
                "name": f"星临者-{index + 1}",
                "kibots": [
                    {
                        "id": f"K{index + 1:02d}-{k + 1:03d}",
                        "element": "火" if k % 4 == 0 else "水",
                        "status": "active" if k % 2 == 0 else "resting",
                        "coordinates": [index * 10 + k, index + k / 10],
                    }
                    for k in range(100)
                ],
            }
        else:
            name = f"星临者-{index + 1}"
            kibots: list[dict] = []
            for start in range(0, KIBOTS_PER_CHARACTER, KIBOT_BATCH_SIZE):
                end = start + KIBOT_BATCH_SIZE
                print(f"生成 {name} 的奇波 {start + 1}-{end} ...", flush=True)
                prompt = (
                    f"为角色 {name} 生成第 {start + 1} 到第 {end} 个奇波 JSON 数组。"
                    f"数组长度必须是 {KIBOT_BATCH_SIZE}。每个对象只能包含 id、element、status、coordinates。"
                    f"id 格式为 K{index + 1:02d}-001 这样的编号，编号范围从 {start + 1:03d} 到 {end:03d}。"
                    f"element 只能从 {ELEMENTS} 中选择；status 只能从 {STATUSES} 中选择；"
                    "coordinates 是两个数字组成的数组。"
                    "请让一部分奇波的 element 为 火，以便后续提取。"
                    "只输出 JSON 数组，不要解释，不要 Markdown。"
                )
                batch = ask_json(
                    prompt,
                    [],
                    mock=False,
                    schema_hint=(
                        f"输出长度为 {KIBOT_BATCH_SIZE} 的数组。"
                        "每项包含 id(str)、element(火/水/风/雷/土)、"
                        "status(active/resting/lost)、coordinates(number[2])。"
                    ),
                    validator=lambda data, count=KIBOT_BATCH_SIZE: validate_kibot_batch(data, count),
                )
                assert isinstance(batch, list)
                kibots.extend(batch)
            character = {"name": name, "kibots": kibots}
            validate_character_chunk(character)

        characters.append(character)

    return characters


def extract_fire_kibot_coordinates(characters: list[dict]) -> list[dict]:
    result = []
    for character in characters:
        for kibot in character.get("kibots", []):
            if kibot.get("element") == "火":
                result.append(
                    {
                        "owner": character.get("name", "未知"),
                        "id": kibot.get("id"),
                        "coordinates": kibot.get("coordinates"),
                    }
                )
    return result


def extract_fire_kibot_coordinates_ai(characters: list[dict], mock: bool) -> list[dict]:
    result: list[dict] = []
    for character in characters:
        print(f"AI 提取 {character.get('name', '未知')} 的火属性奇波坐标 ...", flush=True)
        local_rows = [
            {
                "owner": character.get("name", "未知"),
                "id": kibot.get("id"),
                "coordinates": kibot.get("coordinates"),
            }
            for kibot in character.get("kibots", [])
            if kibot.get("element") == "火"
        ]
        prompt = (
            "下面是一个角色 JSON。请提取其中所有 element 为 火 的奇波，"
            "并重构为 JSON 数组。数组中每个对象只能包含 owner、id、coordinates。"
            "owner 使用角色 name，id 使用奇波 id，coordinates 保留原坐标。"
            "只输出 JSON 数组，不要解释。\n\n"
            f"{json.dumps(character, ensure_ascii=False)}"
        )
        rows = ask_json(
            prompt,
            local_rows,
            mock,
            schema_hint="输出 JSON 数组，每项为 owner(str)、id(str)、coordinates(number[2])。",
            validator=validate_fire_points,
        )
        assert isinstance(rows, list)
        result.extend(rows)
    return result


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="不调用 API，只生成示例数据")
    args = parser.parse_args()

    try:
        simple = simple_generation(args.mock)
        nested = nested_generation(args.mock)
        characters = chunked_generation(args.mock)
        fire_points_ai = extract_fire_kibot_coordinates_ai(characters, args.mock)
    except (GlmError, ValueError) as error:
        print(error)
        print("可以先使用 --mock 查看流程。")
        return

    fire_points = extract_fire_kibot_coordinates(characters)

    OUTPUT_DIR.mkdir(exist_ok=True)
    write_json(OUTPUT_DIR / "simple_character.json", simple)
    write_json(OUTPUT_DIR / "nested_character.json", nested)
    write_jsonl(OUTPUT_DIR / "characters.jsonl", characters)
    write_jsonl(OUTPUT_DIR / "fire_kibot_coordinates.jsonl", fire_points)
    write_jsonl(OUTPUT_DIR / "fire_kibot_coordinates_ai.jsonl", fire_points_ai)

    print("基础 JSON：", simple)
    print("复杂 JSON：", nested)
    print(f"角色数量：{len(characters)}")
    print(f"火属性奇波坐标数量（代码提取）：{len(fire_points)}")
    print(f"火属性奇波坐标数量（AI 提取）：{len(fire_points_ai)}")
    print(f"输出目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
