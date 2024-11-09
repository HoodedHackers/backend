import asyncio
from unittest.mock import Mock

import pytest

from .counter import Counter


@pytest.fixture
def tick_callback():
    return Mock()


@pytest.fixture
def timeout_callback():
    return Mock()


@pytest.fixture
def counter(tick_callback, timeout_callback):
    return Counter(tick_callback, timeout_callback, tick_time=0.1, timeout=0.3)


@pytest.mark.asyncio
async def test_counter_start_and_stop(counter, tick_callback, timeout_callback):
    await counter.start()

    await asyncio.sleep(0.4)

    assert counter.count <= counter.timeout
    tick_callback.assert_called()
    timeout_callback.assert_called_once()


@pytest.mark.asyncio
async def test_counter_tick(counter, tick_callback, timeout_callback):
    await counter.start()

    await asyncio.sleep(0.4)

    assert counter.running
    tick_callback.assert_called()
    timeout_callback.assert_called_once()

    await counter.stop()
    assert not counter.running
