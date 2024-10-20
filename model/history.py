import json
import random
from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy.types import Integer
from typing_extensions import Optional

from database import Base

from .board import Board, Color
from .exceptions import *


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"))
    board: Mapped[List[Color]] = mapped_column(Board, default=Board.random_board)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    fig_mov_id: Mapped[int] = mapped_column(Integer)
    origin_x: Mapped[int] = mapped_column(Integer)
    origin_y: Mapped[int] = mapped_column(Integer)
    dest_x: Mapped[int] = mapped_column(Integer)
    dest_y: Mapped[int] = mapped_column(Integer)

    def __repr__(self):
        return (
            f"<History(id={self.id}, game_id={self.game_id}, board={self.board}, "
            f"player_id={self.player_id}, mov_id={self.mov_id}, origin_x={self.origin_x}, "
            f"origin_y={self.origin_y}, dest_x={self.dest_x}, dest_y={self.dest_y})>"
        )

    def set_defaults(self):
        if self.board is None:
            self.board = Board.random_board()
        if self.player_id is None:
            self.player_id = 1
        if self.mov_id is None:
            self.mov_id = 1
        if self.origin_x is None:
            self.origin_x = 0
        if self.origin_y is None:
            self.origin_y = 0
        if self.dest_x is None:
            self.dest_x = 0
        if self.dest_y is None:
            self.dest_y = 0

    def __eq__(self, other):
        if not isinstance(other, History):
            return NotImplemented
        return (
            self.id == other.id
            and self.game_id == other.game_id
            and self.board == other.board
            and self.player_id == other.player_id
            and self.mov_id == other.mov_id
            and self.origin_x == other.origin_x
            and self.origin_y == other.origin_y
            and self.dest_x == other.dest_x
            and self.dest_y == other.dest_y
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_defaults()

    def to_dict(self):
        return {
            "id": self.id,
            "game": self.game_id,
            "board": self.board,
            "player_id": self.player_id,
            "fig_mov_id": self.fig_mov_id,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "dest_x": self.dest_x,
            "dest_y": self.dest_y,
        }
