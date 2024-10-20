from typing import List, Optional

from sqlalchemy.sql import func

from model import Game, Player
from repositories.general import Repository


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

    def get_available(
        self,
        count: int | None = None,
        max_players: Optional[int] = None,
        name: Optional[str] = None,
    ) -> List[Game]:
        q = (
            self.db.query(Game)
            .outerjoin(Game.players)
            .group_by(Game.id)
            .having(func.count(Player.id) < Game.max_players)
            .filter(Game.started == False)
            .order_by(func.count(Player.id))
        )
        if max_players is not None:
            q = q.having(func.count(Player.id) <= max_players)
        if name is not None:
            q = q.where(Game.name.like(name))
        if count is not None:
            q = q.limit(count)
        return q.all()
