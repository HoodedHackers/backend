import math
from typing import List, Tuple
from sqlalchemy.types import VARCHAR, TypeDecorator
from pydantic import BaseModel
from pydantic.fields import Field
from pydantic.validators import validator

from model.board import SIZE_BOARD

BOARD_MAX_SIDE = math.sqrt(SIZE_BOARD) - 1
BOARD_MIN_SIDE = 0
BUNDLE_MOV = 7
TOTAL_MOV = 49
TOTAL_HAND_MOV = 3

all_dist = {
    # (i+-num, j+-num) si no tiene signo es un valor, no una distancia
    1: [(-+2, -+2)],
    2: [(-+2, +-0), (+-0, -+2)],
    3: [(-+1, +-0), (+-0, -+1)],
    4: [(-+1, -+1)],
    5: [(-2, +1), (-1, -2), (+2, -1), (+1, +2)],
    6: [(-2, -1), (-1, +2), (+2, +1), (+1, -2)],
    7: [
        (BOARD_MIN_SIDE, +-0),
        (+-0, BOARD_MIN_SIDE),
        (BOARD_MAX_SIDE, +-0),
        (+-0, BOARD_MAX_SIDE),
    ],
}

class IdMov(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value: List[int] | None, dialect):
        if value is None:
            return None
        return " ".join(f"{c}" for c in value)

    def process_result_value(self, value, dialect) -> List[int]:
        if value is None:
            return []
        list = value.split(" ")
        return [(int(c)) for c in list]

    @staticmethod
    def total() -> List[int]:
        return [i for i in range(1, TOTAL_MOV+1)]


class MoveCards(BaseModel):
    id: int = Field(..., ge=1, le=TOTAL_MOV, description="ID de la carta")
    dist: List[Tuple[int, int]] = []

    @validator('id')
    def check_valid_id(cls, value):
        """ Valida que el id esté dentro del rango permitido """
        if value < 1 or value > TOTAL_MOV:
            raise ValueError(f"El id {value} está fuera del rango válido (1-{TOTAL_MOV})")
        return value

    def __init__(self, id: int):
        """
        Constructor que inicializa la carta con su id y calcula la distancia (movimientos) de inmediato.
        """
        super().__init__(id=id)
        self.dist = self._calculate_dist()

    def _calculate_dist(self) -> List[Tuple[int, int]]:
        """
        Calcula las distancias (movimientos) basadas en el id.
        Usa el módulo y `BUNDLE_MOV` para determinar el valor en `all_dist`.
        """
        valor = BUNDLE_MOV if self.id % BUNDLE_MOV == 0 else self.id % len(all_dist)
        if valor not in all_dist:
            raise ValueError(f"No se encontraron movimientos para el valor {valor}.")
        return all_dist[valor]

    def describe_card(self):
        """
        Método para describir la carta.
        """
        return f"Carta ID: {self.id}, Movimientos: {self.dist}"