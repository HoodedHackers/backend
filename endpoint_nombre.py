from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import Annotated

from model.player import Player
from main import app, player_repo


class Name(BaseModel):
    name: str = Field(min_length=1, max_length=64)


@app.post("/api/name")
async def take_nickname(nickname: Name) -> Name:
    player_repo.save(Player(name=nickname.name))
    return nickname
