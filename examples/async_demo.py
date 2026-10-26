import asyncio

async def simulate_request(
        name:str,
        delay:float,
)->str:
    print(f"{name} begin")
    await asyncio.sleep(delay)
    print(f"{name} end")
    return name

async def main():

    result = await asyncio.gather(
        simulate_request("A",3),
        simulate_request("B",1),
    )
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
