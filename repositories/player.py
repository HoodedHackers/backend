from typing import Optional, List
from model import Player
from repositories.general import Repository


class PlayerRepository(Repository):

    def save(self, player: Player):
        self.db.add(player)
        self.db.commit()

    def delete(self, player: Player):
        self.db.delete(player)
        self.db.commit()

    def get(self, identifier: str) -> Optional[Player]:
        ret = self.db.query(Player).filter(Player.identifier == identifier)
        return ret.first()

    def get_many(self, count: int) -> List[Player]:
        return self.db.query(Player).limit(count).all()
