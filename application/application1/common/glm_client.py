from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-5.1"
DEFAULT_TIMEOUT = 180
DEFAULT_RETRIES = 2
THINKING_MODEL_PREFIXES = ("glm-5", "glm-4.7", "glm-4.6", "glm-4.5")


class GlmError(RuntimeError):
    pass


def supports_thinking(model: str) -> bool:
    normalized = model.lower()
    return normalized.startswith(THINKING_MODEL_PREFIXES)


def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float = 0.1,
    stream: bool = False,
    thinking: bool = False,
) -> str:
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise GlmError("没有找到 ZHIPUAI_API_KEY，请先在终端设置智谱 API Key。")

    if stream:
        raise GlmError("当前简单封装暂不处理流式响应，请使用 stream=False。")

    selected_model = model or os.getenv("GLM_MODEL", DEFAULT_MODEL)
    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if supports_thinking(selected_model):
        payload["thinking"] = {"type": "enabled" if thinking else "disabled"}
    elif thinking:
        raise GlmError(f"{selected_model} 不支持 thinking 参数，请换用 GLM-4.5 或更新模型。")

    request = Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    timeout = int(os.getenv("GLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
    retries = int(os.getenv("GLM_RETRIES", str(DEFAULT_RETRIES)))
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise GlmError(f"GLM 请求失败：{error.code} {body}") from error
        except URLError as error:
            if attempt == retries:
                raise GlmError(f"无法连接 GLM API：{error.reason}") from error
            time.sleep(2 * (attempt + 1))
        except TimeoutError as error:
            if attempt == retries:
                raise GlmError("GLM 请求超时，可以缩小单次生成的数据块或调大 GLM_TIMEOUT。") from error
            time.sleep(2 * (attempt + 1))

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise GlmError(f"无法读取 GLM 返回内容：{result}") from error
