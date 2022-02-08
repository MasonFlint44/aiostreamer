import asyncio
import pytest
from aiostreamer import Streamer

@pytest.mark.asyncio
async def test_constructor():
    streamer = Streamer()
    assert isinstance(streamer._loop, asyncio.BaseEventLoop)
    assert streamer._pushers == []
    assert streamer._waiters == []
    assert streamer._tasks == []
    assert streamer._gens == []