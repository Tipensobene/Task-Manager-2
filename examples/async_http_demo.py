import asyncio
import httpx


async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. 使用 await client.get 请求 https://example.com/
        #    将返回的响应保存到 response
        response = await client.get("https://example.com/")

        # 2. 检查响应状态
        response.raise_for_status()
        # 3. 打印状态码
        print(response.status_code)
        # 4. 打印 response.text 的前80个字符
        print(response.text[:80])


if __name__ == "__main__":
    asyncio.run(main())