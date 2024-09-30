from model import MoveCards
from repositories import CardsMovRepository


# Esta funcion creara solo un numero limitado de cartas para el primer sprint, pero deberia escalar
def create_all_mov(card_repo: CardsMovRepository):
    for i in range(49):
        new_card = MoveCards(name="Soy Movimiento")
        card_repo.save(new_card)
