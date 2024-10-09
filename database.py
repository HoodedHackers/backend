from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Database:
    def __init__(self, db_uri="sqlite:///:memory:"):
        self.engine = create_engine(
            db_uri, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def get_session(self):
        return self.session()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def close(self):
        self.session.close_all()


class Base(DeclarativeBase):
    pass
