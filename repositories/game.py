from typing import Optional, List
from repositories.general import Repository
from model import Game, Player


class GameRepository(Repository):

    def save(self, game: Game):
        self.db.add(game)
        self.db.commit()

    def delete(self, game: Game):
        self.db.delete(game)
        self.db.commit()

    def get(self, id: int) -> Optional[Game]:
        return self.db.get(Game, id)

    def get_many(self, count: int) -> List[Game]:
        return self.db.query(Game).limit(count).all()

    def get_available(self, count: int) -> List[Game]:
        games = self.db.query(Game).filter(Game.started == False).all()
        return [game for game in games if len(game.players) < game.max_players][:count]
