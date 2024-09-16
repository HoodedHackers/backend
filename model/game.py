from dataclasses import dataclass, field

from player import Player


@dataclass
class Game:
    id: int
    name: str
    players: list[Player] = field(default_factory=list)
    current_player: int = 0
    max_players: int = 4
    min_players: int = 2
    started: bool = False

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
