import asyncio
from typing import AsyncGenerator
import pytest
from unittest.mock import MagicMock
from aiostreamer import Streamer


@pytest.fixture
def loop(event_loop):
    get_mock_loop = MagicMock()
    get_mock_loop.return_value = event_loop
    asyncio.get_running_loop = get_mock_loop


@pytest.fixture
def streamer(loop):
    return Streamer()


@pytest.fixture
def collected():
    return []


@pytest.fixture
def collector(streamer, collected):
    async def _collector():
        async for item in streamer.gen():
            collected.append(item)
    return _collector


@pytest.mark.asyncio
async def test_constructor(streamer):
    assert isinstance(streamer._loop, asyncio.BaseEventLoop)
    assert streamer._pushers == []
    assert streamer._waiters == []
    assert streamer._tasks == []
    assert streamer._gens == []


@pytest.mark.asyncio
async def test_gen(streamer):
    gen_a = streamer.gen()
    assert isinstance(gen_a, AsyncGenerator)
    gen_b = streamer.gen()
    assert isinstance(gen_b, AsyncGenerator)
    assert gen_a != gen_b


@pytest.mark.asyncio
async def test_start_task(streamer):
    fake_task_started = False

    async def fake_task():
        nonlocal fake_task_started
        fake_task_started = True

    await streamer.start_task(fake_task())

    # check that code in fake_task has been executed
    assert fake_task_started == True


@pytest.mark.asyncio
async def test_push(streamer, collector, collected):
    await streamer.start_task(collector())
    await streamer.push(1)
    assert collected == [1]
    await streamer.push(2)
    assert collected == [1, 2]


@pytest.mark.asyncio
async def test_push_emits_to_multiple_subscribers(streamer, collector, collected):
    # start two tasks that will collect values
    await streamer.start_task(collector())
    await streamer.start_task(collector())

    await streamer.push(2)
    assert collected == [2, 2]

    await streamer.push(3)
    assert collected == [2, 2, 3, 3]


@pytest.mark.asyncio
async def test_streamer_is_a_hot_stream(streamer, collector, collected):
    await streamer.push(1)
    assert collected == []

    # subscribers to a hot stream will miss out on previously emitted values
    await streamer.start_task(collector())

    await streamer.push(2)
    assert collected == [2]

@pytest.mark.asyncio
async def test_close(streamer, collector, collected):
    # start two tasks that will collect values
    task_a = await streamer.start_task(collector())
    task_b = await streamer.start_task(collector())

    # ensure both tasks are running
    assert not task_a.done()
    assert not task_b.done()

    # ensure both tasks are collecting values
    await streamer.push(2)
    assert collected == [2, 2]

    await streamer.close()

    # ensure neither tasks are running
    assert task_a.done()
    assert task_b.done()

    # ensure neither tasks are collecting values
    await streamer.push(3)
    assert collected == [2, 2]
