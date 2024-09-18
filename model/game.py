from sqlalchemy import Column
from sqlalchemy.orm.properties import MappedColumn
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Boolean, Integer, String

from database import Base
from .player import Player


class Game:
    id: Column[int] = Column(Integer, primary_key=True)
    name: Column[str] = Column(String(64))
    players: MappedColumn[Player] = MappedColumn(ForeignKey("players.id"))
    current_player: Column[int] = Column(Integer)
    max_players: Column[int] = Column(Integer)
    min_players: Column[int] = Column(Integer)
    started: Column[bool] = Column(Boolean)

    def advance_player(self):
        self.current_player += 1
        if self.current_player == len(self.players):
            self.current_player = 0

    def add_player(self, player):
        if len(self.players) == self.max_players:
            raise GameFull
        self.players.append(player)


class GameFull(BaseException):
    pass
