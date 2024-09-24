from typing import Optional, List
from repositories.general import Repository
from model import Game, Player

from sqlalchemy.sql import func


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

    def get_available(self, count: int = None) -> List[Game]:
        q = (
            self.db.query(Game)
            .outerjoin(Game.players)
            .group_by(Game.id)
            .having(func.count(Player.id) < Game.max_players)
            .filter(Game.started == False)
            .order_by(func.count(Player.id))
        )
        if count is not None:
            q = q.limit(count)
        return q.all()
