import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .mov_cards import MoveCards, DistType, all_dist

class TestMoveCards(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        MoveCards.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
    def close_db(self):
        self.session.close()
        MoveCards.metadata.drop_all(self.engine)
    def test_insert_and_get_dist(self):
        card_mov = MoveCards(id=1, dist=all_dist[2])
        self.session.add(card_mov)
        self.session.commit()
        result = self.session.query(MoveCards).filter_by(id=card_mov.id).first()
        assert result is not None
        self.assertEqual(all_dist[2], result.dist)