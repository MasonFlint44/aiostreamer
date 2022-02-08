import asyncio
from aiostreamer import Streamer
from typing import AsyncIterable

async def printer(gen: AsyncIterable[str]) -> None:
    async for item in gen:
        print(item)
        await asyncio.sleep(1)
        print("sleepy item " + item)

async def main():
    streamer = Streamer()

    await streamer.push("no printers yet")

    await streamer.start_task(printer(streamer.gen()))

    await streamer.push("foo")
    await streamer.push("bar")
    await streamer.push("foobar")

    print(f"currently {len(asyncio.all_tasks())} tasks")

    await streamer.close()

    print(f"currently {len(asyncio.all_tasks())} tasks")


asyncio.run(main())
