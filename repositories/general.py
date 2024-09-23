from sqlalchemy.orm import Session


class Repository:
    def __init__(self, db: Session):
        self.db = db

    def flush(self):
        self.db.flush()
