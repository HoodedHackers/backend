from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.schema import ForeignKey, Table

from database import Base


class FigCards(Base):
    __tablename__ = "figCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
