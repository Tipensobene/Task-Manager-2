import asyncio
import os

import httpx




async def get_embedding(text: str) -> list[float]:
    # 读取密钥、组织请求、发送并解析响应
    ...
    ali_api_key=os.getenv("DASHSCOPE_API_KEY","")
    ali_api_key=ali_api_key.strip()
    if not ali_api_key:
        raise RuntimeError("模型服务未配置API密钥")

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {ali_api_key}",
    }

    payload = {
        "model": "text-embedding-v4",
        "input": text,
        "dimensions": 1024,
        "encoding_format": "float",
    }

    async with httpx.AsyncClient(
        timeout=30.0,
    ) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()
        response_data = response.json()

        vector = response_data["data"][0]["embedding"]

        return vector

async def main():
    vector = await get_embedding("commit 提交当前事务。")
    print("向量维度：", len(vector))
    print("前5个数字：", vector[:5])

if __name__ == "__main__":
    asyncio.run(main())