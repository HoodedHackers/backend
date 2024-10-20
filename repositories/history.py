from typing import List, Optional

from sqlalchemy.sql import func

from model.history import History
from repositories.general import Repository


class HistoryRepository(Repository):

    def save(self, history: History):
        self.db.add(history)
        self.db.commit()

    def delete(self, history: History):
        self.db.delete(history)
        self.db.commit()

    def get(self, id: int) -> Optional[History]:
        return self.db.get(History, id)
