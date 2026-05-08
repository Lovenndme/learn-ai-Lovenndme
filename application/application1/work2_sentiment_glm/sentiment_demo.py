from __future__ import annotations

import argparse
import base64
import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common.glm_client import GlmError, chat


LABELS = ["开心", "难过", "愤怒", "中性"]
VISION_MODEL = "glm-5v-turbo"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
MEMES = {
    "开心": ["happy_01.png", "happy_02.png"],
    "难过": ["sad_01.png", "sad_02.png"],
    "愤怒": ["angry_01.png", "angry_02.png"],
    "中性": ["normal_01.png", "normal_02.png"],
}

SAMPLES = [
    "今天项目终于跑通了，太爽了！",
    "复习了一整天还是不会，感觉有点崩溃。",
    "这个 bug 卡我三个小时，真的很烦。",
    "我下午去图书馆还书。",
]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def build_prompt(text: str) -> list[dict[str, str]]:
    labels = "、".join(LABELS)
    return [
        {
            "role": "system",
            "content": (
                "你是一个情绪分类器。"
                f"你只能从以下标签中选择一个输出：{labels}。"
                "不要解释，不要输出标点，不要输出其他文字。"
            ),
        },
        {"role": "user", "content": text},
    ]


def image_to_api_url(image: str) -> str:
    if image.startswith(("http://", "https://")):
        return image

    path = Path(image).expanduser()
    if not path.exists():
        raise GlmError(f"图片不存在：{path}")
    with path.open("rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def build_image_prompt(image: str) -> list[dict[str, Any]]:
    labels = "、".join(LABELS)
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_to_api_url(image)},
                },
                {
                    "type": "text",
                    "text": (
                        "请分析这张图片或表情包表达的情绪。"
                        f"你只能从以下标签中选择一个输出：{labels}。"
                        "不要解释，不要输出标点，不要输出其他文字。"
                    ),
                },
            ],
        }
    ]


def normalize_label(output: str) -> str:
    cleaned = output.strip().replace("。", "").replace(".", "")
    if cleaned in LABELS:
        return cleaned
    for label in LABELS:
        if label in cleaned:
            return label
    return "中性"


def mock_label(text: str) -> str:
    if any(word in text for word in ["爽", "开心", "太好了", "跑通"]):
        return "开心"
    if any(word in text for word in ["崩溃", "难过", "不会"]):
        return "难过"
    if any(word in text for word in ["烦", "气", "怒"]):
        return "愤怒"
    return "中性"


def classify(text: str, mock: bool = False) -> str:
    if mock:
        return mock_label(text)
    output = chat(build_prompt(text), temperature=0.01)
    return normalize_label(output)


def classify_image(image: str, mock: bool = False) -> str:
    if mock:
        return "中性"
    output = chat(build_image_prompt(image), model=VISION_MODEL, temperature=0.01)
    return normalize_label(output)


def choose_meme(label: str) -> str:
    return random.choice(MEMES[label])


def save_json(filename: str, data: Any) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def iter_images(image_dir: str) -> list[Path]:
    directory = Path(image_dir).expanduser()
    if not directory.exists():
        raise GlmError(f"图片目录不存在：{directory}")
    if not directory.is_dir():
        raise GlmError(f"不是图片目录：{directory}")
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def print_image_result(image: str, label: str, meme: str) -> None:
    print(f"图片：{image}")
    print(f"情绪：{label}")
    print(f"表情包：{meme}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="要分析的一句话")
    parser.add_argument("--image", help="要分析的图片路径或图片 URL")
    parser.add_argument("--image-dir", help="批量分析目录下的图片")
    parser.add_argument("--save-output", action="store_true", help="把运行结果保存到 output 目录")
    parser.add_argument("--mock", action="store_true", help="不调用 API，只演示流程")
    args = parser.parse_args()

    if args.image_dir:
        try:
            images = iter_images(args.image_dir)
            results = []
            for image_path in images:
                image = str(image_path)
                label = classify_image(image, mock=args.mock)
                meme = choose_meme(label)
                print_image_result(image, label, meme)
                results.append(
                    {
                        "image": image,
                        "model": VISION_MODEL,
                        "label": label,
                        "meme": meme,
                    }
                )
        except GlmError as error:
            print(error)
            print("可以先使用 --mock 运行流程，申请 API Key 后再调用真实模型。")
            return

        if args.save_output:
            path = save_json("image_sentiment_results.json", results)
            print(f"结果文件：{path}")
        return

    if args.image:
        try:
            label = classify_image(args.image, mock=args.mock)
        except GlmError as error:
            print(error)
            print("可以先使用 --mock 运行流程，申请 API Key 后再调用真实模型。")
            return

        meme = choose_meme(label)
        print_image_result(args.image, label, meme)
        if args.save_output:
            path = save_json(
                "image_sentiment_result.json",
                {
                    "image": args.image,
                    "model": VISION_MODEL,
                    "label": label,
                    "meme": meme,
                },
            )
            print(f"结果文件：{path}")
        return

    texts = [args.text] if args.text else SAMPLES
    results = []
    for text in texts:
        try:
            label = classify(text, mock=args.mock)
        except GlmError as error:
            print(error)
            print("可以先使用 --mock 运行流程，申请 API Key 后再调用真实模型。")
            return

        meme = choose_meme(label)
        print(f"输入：{text}")
        print(f"情绪：{label}")
        print(f"表情包：{meme}")
        print()
        results.append({"input": text, "label": label, "meme": meme})

    if args.save_output:
        path = save_json("text_sentiment_results.json", results)
        print(f"结果文件：{path}")


if __name__ == "__main__":
    main()
