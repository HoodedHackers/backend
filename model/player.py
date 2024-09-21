from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.types import Integer, String

from database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    host: Mapped[bool] = mapped_column(Integer, default=False, nullable=False)
    on_game: Mapped[bool] = mapped_column(Integer, default=False, nullable=False)
