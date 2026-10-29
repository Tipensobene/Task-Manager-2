import json
import asyncio

from task_candidate import TaskCandidate


chunks = [
    r'data: {"choices":[{"delta":{"role":"assistant"},"finish_reason":null}]}',
    r'data: {"choices":[{"delta":{"content":"{\"title\":\"学习"},"finish_reason":null}]}',
    "",
    r'data: {"choices":[{"delta":{"content":"Python\"}"},"finish_reason":null}]}',
    r'data: {"choices":[{"delta":{"content":""},"finish_reason":"stop"}]}',
    'data: [DONE]',
]



async def simulate_stream():
    for chunk in chunks:
        await asyncio.sleep(1)
        yield chunk


async def main():

    received_chunks = []
    stream_ended = False
    finish_reason = None



    async for line in simulate_stream():
        if not line.startswith("data:"):
            continue

        event_text =  line.removeprefix("data:").strip()

        if event_text == "[DONE]":
            stream_ended = True
            break

        else:
            event = json.loads(event_text)
            content = event["choices"][0]["delta"].get("content")
            finish_reason = event["choices"][0]["finish_reason"]

        if content:
            received_chunks.append(content)
            print(content)

    if not stream_ended:
        raise RuntimeError("流未正常结束，不能生成候选")

    if finish_reason != "stop":
        raise RuntimeError("模型生成未正常完成，不能生成候选")


    # 1. 用 "".join(chunks) 得到完整字符串 answer
    answer="".join(received_chunks)

    # 2. 用 json.loads(answer) 得到字典 data
    data = json.loads(answer)

    # 3. 用 TaskCandidate.model_validate(data) 得到 candidate
    candidate = TaskCandidate.model_validate(data)

    # 4. 打印 candidate.model_dump()
    print(candidate.model_dump())

if __name__ == '__main__':
    asyncio.run(
        main()
    )