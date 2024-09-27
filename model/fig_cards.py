from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Column
from sqlalchemy.types import Integer, String
from sqlalchemy.schema import ForeignKey, Table

from database import Base
from .game import game_player_association

figCards_player_association = Table(
    "figCards_player_association",
    Base.metadata,
    Column("figCards_id", Integer, ForeignKey("figCards.id")),
    Column("player_in_game_id", Integer, ForeignKey("game_player_association.id"))
)


class FigCards(Base):
    __tablename__ = "figCards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))