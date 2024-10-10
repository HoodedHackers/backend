from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import UUID
from sqlalchemy.types import Integer, String

from database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    identifier: Mapped[UUID] = mapped_column(UUID, default=uuid4, index=True)

    def __repr__(self) -> str:
        return (
            f"<Player(id={self.id}, name='{self.name}', identifier={self.identifier})>"
        )
