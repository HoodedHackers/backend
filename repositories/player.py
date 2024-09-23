from typing import Optional, List
from model import Player
from repositories.general import Repository
from sqlalchemy.types import UUID


class PlayerRepository(Repository):

    def save(self, player: Player):
        self.db.add(player)
        self.db.commit()

    def delete(self, player: Player):
        self.db.delete(player)
        self.db.commit()

    def get(self, identifier: UUID) -> Optional[Player]:
        return self.db.get(Player, identifier)

    def get_many(self, count: int) -> List[Player]:
        return self.db.query(Player).limit(count).all()
