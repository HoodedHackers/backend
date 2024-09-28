from typing import List
from sqlalchemy import Column
from sqlalchemy.orm import mapped_column, relationship, Mapped, MappedColumn
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy.types import Boolean, Integer, String

from database import Base
from .player import Player


game_player_association = Table(
    "game_player_association",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("player_id", Integer, ForeignKey("players.id")),
)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    current_player_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    min_players: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    started: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    players: Mapped[List[Player]] = relationship(
        "Player", secondary=game_player_association
    )
    host: Mapped[Player] = relationship("Player", nullable=False)

    def __eq__(self, other):
        if not isinstance(other, Game):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.current_player_turn == other.current_player_turn
            and self.max_players == other.max_players
            and self.min_players == other.min_players
            and self.started == other.started
            and self.players == other.players
        )

    def set_defaults(self):
        if self.current_player_turn is None:
            self.current_player_turn = 0
        if self.max_players is None:
            self.max_players = 4
        if self.min_players is None:
            self.min_players = 2
        if self.started is None:
            self.started = False

    def __repr__(self):
        return (
            f"<Game(id={self.id}, name={self.name}, current_player_turn={self.current_player_turn}, "
            f"max_players={self.max_players}, min_players={self.min_players}, started={self.started})>"
        )

    def advance_player(self):
        self.current_player_turn += 1
        if self.current_player_turn == len(self.players):
            self.current_player_turn = 0

    def add_player(self, player):
        if len(self.players) == self.max_players:
            raise GameFull
        self.players.append(player)

    """
    creo que va aca se agrega el delete del jugador xd
    """

    def delete_player(self, player):
        if player not in self.players:
            raise PlayerNotInGame
        self.players.remove(player)

    """''
    def delete_player(self, player_identifier: str):
        player_remove = next(
            (player for player in self.players if str(player.identifier) == player_identifier), None
        )
        if player_remove is None:
            raise PlayerNotInGame
        self.players.remove(player_remove)
    """ ""


class GameFull(BaseException):
    pass


class PlayerNotInGame(BaseException):
    pass
