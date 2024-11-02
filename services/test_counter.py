import asyncio
from unittest.mock import Mock

import pytest

from .counter import Counter


@pytest.fixture
def tick_callback():
    return Mock()


@pytest.fixture
def stop_callback():
    return Mock()


@pytest.fixture
def counter(tick_callback, stop_callback):
    return Counter(tick_callback, stop_callback, tick_time=0.1, timeout=0.2)


@pytest.mark.asyncio
async def test_counter_start_and_stop(counter, tick_callback, stop_callback):
    await counter.start()

    await asyncio.sleep(0.3)

    assert counter.count >= counter.timeout
    assert not counter.running
    tick_callback.assert_called()
    stop_callback.assert_called_once()


@pytest.mark.asyncio
async def test_counter_tick(counter, tick_callback, stop_callback):
    await counter.start()

    await asyncio.sleep(0.2)

    assert counter.count > 0
    assert counter.running
    tick_callback.assert_called()
    stop_callback.assert_not_called()

    await counter.stop()
    assert not counter.running
    stop_callback.assert_called_once()
