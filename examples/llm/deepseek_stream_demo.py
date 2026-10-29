import asyncio
import os
import json
import httpx
from pydantic import ValidationError

from task_candidate import TaskCandidate


# 应用层保护值，不是模型平台的限制。
MAX_EVENT_CHARS = 65536
MAX_ANSWER_CHARS = 65536
STREAM_TIMEOUT_SECONDS = 120


async def iter_sse_data(response):
    """按空行组装SSE事件；同一事件的多条data行用换行连接。"""
    data_lines = []
    event_size = 0
    first_line = True
    async for line in response.aiter_lines():
        if first_line:
            line = line.removeprefix("\ufeff")
            first_line = False
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
            data_lines = []
            event_size = 0
            continue
        if line.startswith(":"):
            continue  # SSE注释/心跳没有候选内容。
        field, _, value = line.partition(":")
        if field != "data":
            continue  # 本次单次请求不使用event/id/retry等字段。
        value = value.removeprefix(" ")  # 协议只移除冒号后的一个空格。
        event_size += len(value) + 1
        if event_size > MAX_EVENT_CHARS:
            raise RuntimeError("模型流式事件过大")
        data_lines.append(value)
    if data_lines:
        raise RuntimeError("模型流式事件未完整结束")


def parse_stream_event(event_text):
    """返回(content, finish_reason)；纯用量事件返回None。"""
    try:
        event = json.loads(event_text)
    except json.JSONDecodeError as error:
        raise RuntimeError("模型流式事件不是合法JSON") from error
    if not isinstance(event, dict):
        raise RuntimeError("模型流式事件必须是对象")
    if "error" in event:
        raise RuntimeError("模型服务返回流式错误事件")
    try:
        choices = event["choices"]
        if not isinstance(choices, list):
            raise RuntimeError("模型流式事件的choices必须是列表")
        if not choices and isinstance(event.get("usage"), dict):
            return None  # 兼容纯用量事件，不将它当作正文或完成标记。
        if not choices:
            raise RuntimeError("模型流式事件缺少候选选项")
        if len(choices) != 1:
            raise RuntimeError("当前示例只支持一个候选选项")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise RuntimeError("模型流式事件的choice必须是对象")
        index = choice.get("index", 0)
        if type(index) is not int or index != 0:
            raise RuntimeError("模型流式事件的候选索引不合法")
        delta = choice["delta"]
        if not isinstance(delta, dict):
            raise RuntimeError("模型流式事件的delta必须是对象")
        content = delta.get("content")
        reason = choice["finish_reason"]
    except KeyError as error:
        raise RuntimeError("模型流式事件缺少必要结构") from error


    if content is not None and not isinstance(content, str):
        raise RuntimeError("模型流式正文片段必须是字符串或null")

    if reason is not None and not isinstance(reason, str):
        raise RuntimeError("模型流式结束原因必须是字符串或null")
    return content, reason


async def collect_candidate(response):
    """只在流完整结束、正文及字段均合法时返回候选。"""
    received_chunks = []
    answer_size = 0
    stream_ended = False
    finish_reason = None
    async for event_text in iter_sse_data(response):
        if event_text.strip() == "[DONE]":
            stream_ended = True
            break
        parsed = parse_stream_event(event_text)
        if parsed is None:
            continue
        content, current_reason = parsed
        if finish_reason is not None and content:
            raise RuntimeError("模型结束后仍返回正文")
        if current_reason is not None:
            if current_reason != "stop":
                raise RuntimeError("模型生成未正常完成，不能生成候选")
            finish_reason = current_reason
        if content:
            answer_size += len(content)
            if answer_size > MAX_ANSWER_CHARS:
                raise RuntimeError("模型回答过长")
            received_chunks.append(content)
            print(content)
    if not stream_ended:
        raise RuntimeError("流未正常结束，不能生成候选")
    if finish_reason != "stop":
        raise RuntimeError("模型生成未正常完成，不能生成候选")
    answer = "".join(received_chunks)
    if not answer.strip():
        raise RuntimeError("模型回答不能为空")
    try:
        data = json.loads(answer)
    except json.JSONDecodeError as error:
        raise RuntimeError("模型回答不是合法JSON") from error
    try:
        return TaskCandidate.model_validate(data)
    except ValidationError as error:
        raise RuntimeError("模型候选任务字段不合法") from error


async def main():
    text = "高优先级学习Python，备注是练习流式响应。"

    # 在这里准备密钥、地址、请求头、Schema和请求体
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    api_key=api_key.strip()
    if not api_key:
        raise RuntimeError("模型服务未配置API密钥")

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    schema_text = json.dumps(
        TaskCandidate.model_json_schema(),
        ensure_ascii=False,
    )

    payload = {
        "model": "deepseek-flash",
        "messages": [
            {
                "role": "system",
                "content": """
        你负责从用户的一句话中提取一条候选任务。
        只返回一个JSON对象，不要使用Markdown代码块，不要添加解释。

        字段规则：
        title：从用户输入中提取任务标题。
        priority：根据用户表达确定优先级，未说明时使用normal。
        tags：提取用户提供的标签，未说明时使用空列表.
        description：提取用户提供的备注，未说明时使用空字符串

        输出格式示例：
        {"title":"阅读文档","priority":"normal","tags":[],"description":""}
        """
        +
        "\n候选任务应符合以下JSON Schema：\n"
        +
        schema_text,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": True,
        "response_format": {"type": "json_object"},
        "max_tokens":2048,
    }

    print("密钥已配置：", bool(api_key))
    print("请求模型：", payload["model"])
    print("流式请求：", payload["stream"])

    timeout = httpx.Timeout(
        20.0,
        connect=10.0,
    )

    try:
        # 总时限避免持续心跳让请求无限延长；取消时仍退出上下文。
        async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST", url, headers=headers, json=payload,
                ) as response:
                    response.raise_for_status()
                    media_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if media_type.strip().lower() != "text/event-stream":
                        raise RuntimeError("模型响应不是SSE事件流")
                    response.encoding = "utf-8"
                    print(response.status_code)
                    candidate = await collect_candidate(response)
    except httpx.HTTPError as error:
        raise RuntimeError("模型流式请求或读取失败") from error
    except TimeoutError as error:
        raise RuntimeError("模型流式请求超过总时限") from error

    print(candidate.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
