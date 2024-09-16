from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import Annotated 

app = FastAPI()

class Name(BaseModel):
    name: str = Field(min_length=1, max_length=25)

@app.post("/api/name")
async def take_nickname(nickname: Name) -> Name:
    return nickname