import os
import requests
import json
from task_candidate import TaskCandidate
from pydantic import ValidationError


def generate_candidate(
        text: str,
) -> TaskCandidate:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()
    if not text:
        raise ValueError("text cannot be empty")

    if len(text) > 2000:
        raise ValueError("text cannot be longer than 2000 characters")


    api_key=os.getenv("DEEPSEEK_API_KEY","")
    api_key=api_key.strip()
    if not api_key:
        raise RuntimeError("模型服务未配置API密钥")

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "deepseek-flash",
        "messages": [
            {
                "role": "system",
                "content": """
        你负责从用户的一句话中提取一条候选任务。
        只返回一个JSON对象，不要使用Markdown代码块，不要添加解释。

        字段规则：
        title：任务标题，字符串。
        priority：只能是low、normal、high，未说明时使用normal。
        tags：字符串列表，未说明时使用空列表。
        description：备注字符串，未说明时使用空字符串。
        不要生成id、done或created_at。

        输出格式示例：
        {"title":"阅读文档","priority":"normal","tags":[],"description":""}
        """,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=(10, 20),

        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError("模型服务请求失败") from error

    try:
        response_data = response.json()

    except requests.exceptions.JSONDecodeError as error:
        raise RuntimeError("模型服务响应不是合法JSON") from error

    try:
        answer = response_data["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("模型服务响应缺少有效回答结构") from error

    if not isinstance(answer, str):
        raise RuntimeError("answer must be a string")

    answer = answer.strip()
    if not answer:
        raise RuntimeError("answer cannot be empty")

    try:
        candidate = json.loads(answer)

    except json.JSONDecodeError as error:
        raise RuntimeError("模型回答不是合法JSON") from error

    try:
        validated_candidate = TaskCandidate.model_validate(candidate)

    except ValidationError as error:
        raise RuntimeError("模型候选任务字段不合法") from error

    return validated_candidate



