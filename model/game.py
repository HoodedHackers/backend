import copy
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from sqlalchemy import Column
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, Table
from sqlalchemy.sql.type_api import TypeDecorator
from sqlalchemy.types import VARCHAR, Boolean, Integer, String
from typing_extensions import Optional

from database import Base
from model import TOTAL_FIG_CARDS, TOTAL_HAND_FIG
from model.fig_cards import TOTAL_FIG_CARDS, all_coord
from model.figure_search import CandidateShape, Figure, find_figures

from .board import Board, Color
from .exceptions import *
from .mov_cards import IdMov
from .player import Player

TOTAL_NUM_HAND = 3
DECK_SIZE = 50

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
    mov_parcial: List[int]
    block_card: int

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "turn_position": self.turn_position,
            "hand_fig": self.hand_fig,
            "hand_mov": self.hand_mov,
            "fig": self.fig,
            "mov_parcial": self.mov_parcial,
            "block_card": self.block_card,
        }

    @staticmethod
    def from_dict(data: dict):
        return PlayerInfo(
            player_id=data["player_id"],
            turn_position=data["turn_position"],
            hand_fig=data["hand_fig"],
            hand_mov=data["hand_mov"],
            fig=data["fig"],
            mov_parcial=data["mov_parcial"],
            block_card=data["block_card"],
        )

    def copy(self):
        return copy.deepcopy(self)


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
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

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
                    mov_parcial=[],
                    block_card=0,
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
            and self.is_private == other.is_private
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
            f"host_id={self.host_id}, is_private={self.is_private})>"
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
            fig=[],
            mov_parcial=[],
            block_card=0,
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

    def get_player_in_game(self, position: int) -> Player:
        return self.players[position]

    def get_player_hand_movs(self, player_id: int) -> List[int]:
        return self.player_info[player_id].hand_mov

    def get_player_mov_parcial(self, player_id: int):
        return self.player_info[player_id].mov_parcial

    def get_player_hand_figures(self, player_id: int) -> List[int]:
        return self.player_info[player_id].hand_fig

    def get_player_figures(self, player_id: int) -> List[int]:
        return self.player_info[player_id].fig

    def get_card_block(self, other_player: int):
        return self.player_info[other_player].block_card

    def add_hand_mov(self, new_cards, discard, id):
        self.player_info[id] = PlayerInfo(
            player_id=id,
            turn_position=self.player_info[id].turn_position,
            hand_fig=self.player_info[id].hand_fig,
            hand_mov=new_cards,
            fig=self.player_info[id].fig,
            mov_parcial=self.player_info[id].mov_parcial,
            block_card=self.player_info[id].block_card,
        )
        self.all_movs = [x for x in self.all_movs if x not in discard]

    def deal_card_mov(self, player_id: int):
        mov_hand = self.get_player_hand_movs(player_id)
        count = TOTAL_NUM_HAND - len(mov_hand)
        movs_in_self = self.all_movs
        conjunto = set()
        while len(conjunto) < count:
            conjunto.add(random.choice(movs_in_self))
        cards = list(conjunto)
        mov_hand.extend(cards)
        self.add_hand_mov(mov_hand, cards, player_id)
        return mov_hand

    def add_single_mov(self, player_id, card_id):
        aux_parcial = self.player_info[player_id].copy()
        aux_parcial.mov_parcial.append(card_id)
        self.player_info[player_id] = aux_parcial
        cards_left = [
            x
            for x in self.player_info[player_id].hand_mov
            if x not in aux_parcial.mov_parcial
        ]
        return cards_left

    def remove_single_mov(self, player_id: int, card_id: int):
        aux_parcial = self.player_info[player_id].copy()
        aux_parcial.mov_parcial.remove(card_id)
        self.player_info[player_id] = aux_parcial
        cards_left = [
            x
            for x in self.player_info[player_id].hand_mov
            if x not in aux_parcial.mov_parcial
        ]
        return cards_left

    def discard_card_movement(self, player_id: int):
        list_parcial = self.player_info[player_id].mov_parcial
        aux_player_info = self.player_info[player_id].copy()
        for card in list_parcial:
            aux_player_info.hand_mov.remove(card)
            aux_player_info.mov_parcial.remove(card)
        self.player_info[player_id] = aux_player_info

    def clear_mov_parcial(self, player_id: int):
        aux_player_info = self.player_info[player_id].copy()
        aux_player_info.mov_parcial = []
        self.player_info[player_id] = aux_player_info

    # falta verificar si el hand_fig es vacio o si fig es vacio (si es ambos en ese caso gana)
    def add_random_card(self, player_id: int):
        if len(self.player_info[player_id].hand_fig) == TOTAL_HAND_FIG:
            return self.player_info[player_id].hand_fig

        if len(self.player_info[player_id].fig) and (
            not self.player_info[player_id].block_card
        ):
            cards_hand_fig = self.player_info[player_id].hand_fig
            needs_cards = len(cards_hand_fig)
            count = TOTAL_HAND_FIG - needs_cards
            for _ in range(count):
                if not self.player_info[player_id].fig:
                    break
                id = random.choice(self.player_info[player_id].fig)

                aux_hand_fig = self.player_info[player_id].hand_fig
                aux_fig = self.player_info[player_id].fig
                aux_fig.remove(id)
                aux_hand_fig.append(id)
                self.player_info[player_id] = PlayerInfo(
                    player_id=player_id,
                    turn_position=self.player_info[player_id].turn_position,
                    hand_fig=aux_hand_fig,
                    hand_mov=self.player_info[player_id].hand_mov,
                    fig=aux_fig,
                    mov_parcial=self.player_info[player_id].mov_parcial,
                    block_card=self.player_info[player_id].block_card,
                )
            return self.player_info[player_id].hand_fig
        else:
            return self.player_info[player_id].hand_fig

    def swap_tiles(self, origin_x: int, origin_y: int, dest_x: int, dest_y: int):
        origin_index = origin_x + origin_y * 6
        dest_index = dest_x + dest_y * 6

        origin_color = self.board[origin_index]
        dest_color = self.board[dest_index]

        aux = self.board.copy()
        aux[origin_index] = dest_color
        aux[dest_index] = origin_color
        self.board = aux

    def discard_card_hand_figures(self, player_id: int, card: int):
        left_one = len(self.player_info[player_id].hand_fig) - 1
        card_block = self.player_info[player_id].block_card
        if card in self.player_info[player_id].hand_fig:
            # new_player_info = self.player_info[player_id].copy()
            new_player_info = self.player_info[player_id].hand_fig
            new_player_info.remove(card)
            if card_block and (left_one == 0):
                # new_player_info.block_card = 0
                self.player_info[player_id] = PlayerInfo(
                    player_id=player_id,
                    turn_position=self.player_info[player_id].turn_position,
                    hand_fig=self.player_info[player_id].hand_fig,
                    hand_mov=self.player_info[player_id].hand_mov,
                    fig=self.player_info[player_id].fig,
                    mov_parcial=self.player_info[player_id].mov_parcial,
                    block_card=0,
                )
            self.player_info[player_id] = PlayerInfo(
                player_id=player_id,
                turn_position=self.player_info[player_id].turn_position,
                hand_fig=new_player_info,
                hand_mov=self.player_info[player_id].hand_mov,
                fig=self.player_info[player_id].fig,
                mov_parcial=self.player_info[player_id].mov_parcial,
                block_card=self.player_info[player_id].block_card,
            )
            hand_fig = self.player_info[player_id].hand_fig
        else:
            hand_fig = self.player_info[player_id].hand_fig
        return hand_fig

    def get_possible_figures(self, player_id: int) -> List[CandidateShape]:
        player_figures = []
        for fig_id in self.player_info[player_id].hand_fig:
            if fig_id % TOTAL_FIG_CARDS == 0:
                id_coord = TOTAL_FIG_CARDS
            else:
                id_coord = fig_id % TOTAL_FIG_CARDS
            new_figure = Figure(fig_id, all_coord[id_coord])
            player_figures.append(new_figure)
        return find_figures(self.board, player_figures)

    def block_card(self, other_player: int, card_block: int):
        new_player_info = self.player_info[other_player].copy()
        new_player_info.block_card = card_block
        self.player_info[other_player] = new_player_info

    def distribute_deck(self):
        players = len(self.players)
        count_deck = DECK_SIZE // players
        all_figs_cards = list(range(1, 51))
        for players in self.players:
            new_player_info = self.player_info[players.id].copy()
            new_fig = []
            while len(new_fig) < count_deck:
                card_fig = random.choice(all_figs_cards)
                if card_fig in all_figs_cards:
                    all_figs_cards.remove(card_fig)
                    new_fig.append(card_fig)
            new_player_info.fig = new_fig
            self.player_info[players.id] = new_player_info

    def ids_get_possible_figures(self, player_id: int) -> List[int]:
        return [c.figure_id() for c in self.get_possible_figures(player_id)]
