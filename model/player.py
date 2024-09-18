from sqlalchemy import Column
from sqlalchemy.types import Integer, String

from database import Base

class Player(Base):
    __tablename__ = "players"

    id: Column[int] = Column(Integer, primary_key=True)
    name: Column[str] = Column(String(64))
