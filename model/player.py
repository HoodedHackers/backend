from uuid import uuid4

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql.sqltypes import UUID
from sqlalchemy.types import Integer, String

from database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    identifier: Mapped[UUID] = mapped_column(UUID, default=uuid4, index=True)
