from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import Integer, String

from database import Base

class MoveCards(Base):
    __tablename__ = "moveCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))