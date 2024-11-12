import unittest
from collections import Counter, defaultdict

from sqlalchemy import Integer, create_engine, text
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker

from .board import Board, Color


class Base(DeclarativeBase):
    pass


class Dummy(Base):
    __tablename__ = "dummy"
    id = mapped_column(Integer, primary_key=True)
    board = mapped_column(Board)


class TestCommaSeparatedListType(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_insert_and_get_board(self):
        board = [Color.RED, Color.BLUE, Color.BLUE, Color.YELLOW, Color.GREEN]
        d = Dummy(board=board, id=1)
        self.session.add(d)
        self.session.commit()
        result = self.session.query(Dummy).filter_by(id=d.id).first()
        assert result is not None
        self.assertEqual(board, result.board)

    def test_representation(self):
        board = "111432"
        mem_board = [
            Color.RED,
            Color.RED,
            Color.RED,
            Color.BLUE,
            Color.GREEN,
            Color.YELLOW,
        ]
        self.session.execute(text(f"INSERT INTO dummy (id, board) VALUES (1, {board})"))
        result = self.session.query(Dummy).filter_by(id=1).first()
        assert result is not None
        self.assertEqual(mem_board, result.board)


class TestBoard(unittest.TestCase):
    def test_random_board_count(self):
        board = Board.random_board()
        self.assertEqual(len(board), 36)
        count = Counter(board)
        for _, count in count.items():
            self.assertEqual(count, 9)
