import asyncio
from typing import Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import WebSocket, WebSocketDisconnect


class Counter:
    def __init__(
        self, tick_callback, stop_callback, tick_time: float = 0.5, timeout: float = 120
    ):
        self.scheduler = AsyncIOScheduler()
        self.count = 0
        self.running = False
        self.timeout = timeout
        self.tick_callback = tick_callback
        self.stop_callback = stop_callback
        self.tick_time = tick_time

    async def count_up(self):
        self.count += self.tick_time
        self.tick_callback(self.count)
        if self.count >= self.timeout:
            await self.stop()

    async def start(self):
        self.running = True
        self.scheduler.add_job(self.count_up, "interval", seconds=self.tick_time)
        self.scheduler.start()

    async def stop(self):
        if self.running:
            self.running = False
            self.scheduler.shutdown(wait=False)
            self.stop_callback()


class CounterManager:
    lobbies: Dict[int, Counter]

    @classmethod
    def get_counter(cls, game_id: int) -> Optional[Counter]:
        return CounterManager.lobbies.get(game_id)

    @classmethod
    async def delete_counter(cls, game_id: int):
        if game_id in CounterManager.lobbies:
            counter = CounterManager.lobbies[game_id]
            await counter.stop()
            del CounterManager.lobbies[game_id]

    @classmethod
    def add_counter(cls, game_id: int, counter: Counter):
        CounterManager.lobbies[game_id] = counter
