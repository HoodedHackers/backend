from model import FigCards
from repositories import FigRepository


# Esta funcion creara solo un numero limitado de cartas para el primer sprint, pero deberia escalar
def create_all_figs(card_repo: FigRepository):
    for i in range(12):
        new_card = FigCards(name="Soy Figura")
        card_repo.save(new_card)
