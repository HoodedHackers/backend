import asyncio
from fastapi import WebSocket


class Counter:
    def __init__(self):
        self.count = 0
        self.running = False
        self.websocket = None

    async def start(self, websocket: WebSocket):
        self.running = True
        self.websocket = websocket
        while self.running:
            await asyncio.sleep(1)
            self.count += 1

            if self.count >= 120:
                await websocket.send_json({"message": "Timeout"})
                await self.stop()

    async def stop(self):
        self.running = False
