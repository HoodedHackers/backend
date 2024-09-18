from fastapi import FastAPI, Response, Request, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, Base, engine
from model import Player

Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


def get_db(request: Request):
    return request.state.db


# endpoing juguete, borralo cuando haya uno de verdad
@app.get("/api/borrame")
async def borrame(db: Session = Depends(get_db)):
    players = db.query(Player).limit(10).all()
    return {"players": players}
