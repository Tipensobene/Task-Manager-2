import asyncio
import httpx

async def main():

    async with httpx.AsyncClient(timeout=10.0) as client:

        async with client.stream(
            "GET",
            "https://example.com/",
        ) as response:

            response.raise_for_status()
            print(response.status_code)

            async for line in response.aiter_lines():
                print(line)


if __name__ == '__main__':
    asyncio.run(main())