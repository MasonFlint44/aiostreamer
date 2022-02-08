import asyncio
from typing import Awaitable, Generic, TypeVar, AsyncIterable, List, Any

T = TypeVar('T')

class Streamer(Generic[T]):
    def __init__(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._pushers = []
        self._waiters = []
        self._tasks = []
        self._gens = []

    def gen(self) -> AsyncIterable[T]:
        async def _gen() -> AsyncIterable[T]:
            while True:
                self._set_futures(self._waiters, True)
                fut = self._loop.create_future()
                self._pushers.append(fut)
                try:
                    yield await fut
                finally:
                    self._pushers.remove(fut)

        gen = _gen()
        self._gens.append(gen)
        return gen

    async def push(self, item: T) -> None:
        self._set_futures(self._pushers, item)
        if len(self._gens) == 0:
            return
        fut = self._loop.create_future()
        self._waiters.append(fut)
        try:
            await fut
        finally:
            self._waiters.remove(fut)

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        await asyncio.gather(*[gen.aclose() for gen in self._gens])
        self._gens.clear()

    def _set_futures(self, futures: List[asyncio.Future], item: Any):
        for fut in futures:
            if not fut.done():
                fut.set_result(item)

    async def start_task(self, coro: Awaitable) -> asyncio.Task:
        async def wrapper(fut: asyncio.Future, coro: Awaitable) -> None:
            fut.set_result(True)
            await coro
        
        fut = self._loop.create_future()
        task = asyncio.create_task(wrapper(fut, coro))
        self._tasks.append(task)
        await fut
        return task
