import json
import random
from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy import Column
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy.sql.type_api import TypeDecorator
from sqlalchemy.types import VARCHAR, Boolean, Integer, String
from typing_extensions import Optional

from database import Base
from model import TOTAL_FIG_CARDS, TOTAL_HAND_FIG
from model.fig_cards import all_coord
from model.figure_search import CandidateShape, Figure, find_figures

from .board import Board, Color
from .exceptions import *
from .mov_cards import IdMov
from .player import Player

TOTAL_NUM_HAND = 3
game_player_association = Table(
    "game_player_association",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("player_id", Integer, ForeignKey("players.id")),
)


@dataclass
class PlayerInfo:
    player_id: int
    turn_position: int
    hand_fig: List[int]
    hand_mov: List[int]
    fig: List[int]

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "turn_position": self.turn_position,
            "hand_fig": self.hand_fig,
            "hand_mov": self.hand_mov,
            "fig": self.fig,
        }

    @staticmethod
    def from_dict(data: dict):
        return PlayerInfo(
            player_id=data["player_id"],
            turn_position=data["turn_position"],
            hand_fig=data["hand_fig"],
            hand_mov=data["hand_mov"],
            fig=data["fig"],
        )


class PlayerInfoMapper(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value: Dict[int, PlayerInfo] | None, dialect):
        if value is None:
            return "{}"
        return json.dumps({k: v.to_dict() for k, v in value.items()})

    def process_result_value(self, value, dialect) -> Dict[int, PlayerInfo]:
        if value is None:
            return {}
        return {int(k): PlayerInfo.from_dict(v) for k, v in json.loads(value).items()}


# Necesario para que sqlalchemy se de cuenta que el dict puede cambiar, sino no puede
# darse cuenta cuando se modifica el dict y por ende no persiste cambios a la db.
MutableDict.associate_with(PlayerInfoMapper)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    current_player_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    min_players: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    started: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    players: Mapped[List[Player]] = relationship(
        "Player",
        secondary=game_player_association,
    )
    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False
    )
    host: Mapped[Player] = relationship("Player")
    board: Mapped[List[Color]] = mapped_column(Board, default=Board.random_board)
    player_info: Mapped[Dict[int, PlayerInfo]] = mapped_column(
        PlayerInfoMapper, default=lambda: {}
    )
    all_movs: Mapped[List[int]] = mapped_column(IdMov, default=IdMov.total)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.player_info is None or self.player_info == {}:
            self.player_info = {}
            for index, player in enumerate(self.players):
                self.player_info[player.id] = PlayerInfo(
                    player_id=player.id,
                    turn_position=index,
                    hand_fig=[],
                    hand_mov=[],
                    fig=[],
                )

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
        if self.host_id is None:
            self.host_id = 1
        if self.board is None:
            self.board = Board.random_board()
        if self.all_movs is None:
            self.all_movs = IdMov.total()

    def __repr__(self):
        return (
            f"<Game(id={self.id}, name={self.name}, current_player_turn={self.current_player_turn}, "
            f"max_players={self.max_players}, min_players={self.min_players}, started={self.started}, "
            f"host_id={self.host_id})>"
        )

    def advance_player(self):
        self.current_player_turn += 1
        if self.current_player_turn == len(self.players):
            self.current_player_turn = 0

    def add_player(self, player):
        if len(self.players) == self.max_players:
            raise GameFull
        if self.started:
            raise GameStarted
        self.players.append(player)
        self.player_info[player.id] = PlayerInfo(
            player_id=player.id,
            turn_position=len(self.players) - 1,
            hand_fig=[],
            hand_mov=[],
            fig=list(range(1, TOTAL_FIG_CARDS + 1)),
        )

    def count_players(self) -> int:
        return len(self.players)

    def delete_player(self, player):
        if player not in self.players:
            raise PlayerNotInGame
        self.players.remove(player)
        pos = self.player_info[player.id].turn_position
        del self.player_info[player.id]
        if self.started:
            return
        higher_turns = filter(
            lambda x: x.turn_position > pos, self.player_info.values()
        )
        for info in higher_turns:
            info.turn_position -= 1
            self.player_info[info.player_id] = info

    def current_player(self) -> Optional[Player]:
        if len(self.players) == 0:
            return None
        return self.players[self.current_player_turn]

    def advance_turn(self):
        if not self.started:
            raise PreconditionsNotMet
        self.advance_player()

    def ordered_players(self) -> List[Player]:
        players = {player.id: player for player in self.players}
        order = {
            info.turn_position: info.player_id for info in self.player_info.values()
        }
        return [players[order[i]] for i in range(len(order))]

    def shuffle_players(self):
        order = list(range(0, len(self.players)))
        random.shuffle(order)
        for player, position in zip(self.player_info.values(), order):
            player.turn_position = position

    def start(self):
        if self.started:
            raise GameStarted
        if self.count_players() < self.min_players:
            raise PreconditionsNotMet
        self.board = Board.random_board()
        self.started = True

    def add_hand_mov(self, new_cards, discard, id):
        turn = self.player_info[id].turn_position
        self.player_info[id] = PlayerInfo(
            player_id=id,
            turn_position=turn,
            hand_mov=new_cards,
            hand_fig=self.player_info[id].hand_fig,
            fig=self.player_info[id].fig,
        )
        principal = self.all_movs
        res = [x for x in principal if x not in discard]
        self.all_movs = res

    def get_player_hand_figures(self, player_id: int) -> List[int]:
        return self.player_info[player_id].hand_fig

    def get_player_figures(self, player_id: int) -> List[int]:
        return self.player_info[player_id].fig

    # falta verificar si el hand_fig es vacio o si fig es vacio (si es ambos en ese caso gana)
    def add_random_card(self, player_id: int):
        if len(self.player_info[player_id].hand_fig) == TOTAL_HAND_FIG:
            return self.player_info[player_id].hand_fig

        if len(self.player_info[player_id].fig) != 0:
            cards_hand_fig = self.player_info[player_id].hand_fig
            needs_cards = len(cards_hand_fig)
            count = TOTAL_HAND_FIG - needs_cards
            for _ in range(count):
                if not self.player_info[player_id].fig:
                    break
                id = random.choice(self.player_info[player_id].fig)
                self.player_info[player_id].fig.remove(id)
                self.player_info[player_id].hand_fig.append(id)

            return self.player_info[player_id].hand_fig
        else:
            return self.player_info[player_id].hand_fig

    def get_player_hand_movs(self, player_id: int) -> List[int]:
        return self.player_info[player_id].hand_mov

    def discard_card_hand_figures(self, player_id: int, card: int):
        self.player_info[player_id].hand_fig.remove(card)
        return self.player_info[player_id].hand_fig

    def get_player_in_game(self, position: int) -> Player:
        return self.players[position]

    def get_possible_figures(self, player_id: int) -> List[CandidateShape]:
        player_figures = [
            Figure(fig_id, all_coord[fig_id])
            for fig_id in self.player_info[player_id].hand_fig
        ]
        return find_figures(self.board, player_figures)
