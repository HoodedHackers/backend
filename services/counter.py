import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from repositories.game import GameRepository
from services.connection_manager import ConnectionManager


class Counter:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.count = 0
        self.running = False
        self.timeout = 120

    def set_timeout(self, timeout: int):
        self.timeout = timeout

    async def count_up(self, manager: ConnectionManager, id_game: int):
        self.count += 0.5
        if self.count >= self.timeout:
            await self.stop(manager, id_game)

    async def start(self, id_game: int, manager: ConnectionManager):
        self.running = True
        self.scheduler.add_job(self.count_up(manager, id_game), "interval", seconds=0.5)
        self.scheduler.start()

    async def stop(self, manager: ConnectionManager, id_game: int):
        if self.running:
            self.running = False
            self.scheduler.shutdown(wait=False)
            await manager.broadcast({"event": "timeOut"}, id_game)

    async def listen(
        self,
        websocket: WebSocket,
        id_game: int,
        manager: ConnectionManager,
        repo_game: GameRepository,
    ):
        await websocket.accept()
        try:
            while True:
                message = await websocket.receive_json()
                is_start = message.get("action")
                if is_start != "start":
                    raise HTTPException(status_code=400, detail="The action is invalid")
                game = repo_game.get(id_game)
                if game is None:
                    raise HTTPException(status_code=404, detail="Game not found")

                await self.start(id_game, manager)

        except WebSocketDisconnect:
            if id_game is not None:
                await self.stop(manager, id_game)
