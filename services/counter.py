import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import WebSocket, WebSocketDisconnect


class Counter:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.count = 0
        self.running = False
        self.websocket = None
        self.timeout = 120

    def set_timeout(self, timeout: int):
        self.timeout = timeout

    async def count_up(self):
        self.count += 0.5
        if self.count >= self.timeout:
            if self.websocket:
                await self.websocket.send_json({"message": "Timeout"})
            await self.stop()

    async def start(self, websocket: WebSocket):
        self.running = True
        self.websocket = websocket
        self.scheduler.add_job(self.count_up, "interval", seconds=0.5)
        self.scheduler.start()

    async def stop(self):
        if self.running:
            self.running = False
            self.scheduler.shutdown(wait=False)
            if self.websocket:
                await self.websocket.send_json({"message": "Timer stopped"})

    async def listen(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:  # Escucha indefinidamente
                message = await websocket.receive_json()
                if message.get("action") == "start":
                    await self.start(websocket)
                elif message.get("action") == "stop":
                    await self.stop()
                else:
                    await websocket.send_json({"error": "Unknown action"})
        except WebSocketDisconnect:
            await self.stop()
