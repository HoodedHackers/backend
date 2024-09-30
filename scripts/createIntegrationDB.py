import argparse
import logging

from database import Database
from model import Game, Player
from repositories import PlayerRepository, GameRepository


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Crea una base de datos compatible con el entorno del back con data de juguete"
    )
    parser.add_argument(
        "--dbpath",
        type=str,
        required=True,
        help="El path al archivo de base de datos. Ej: sqlite://./local.db",
    )
    args = parser.parse_args()
    logging.info("Conectando a la base de datos en %s", args.dbpath)
    dbs = Database(args.dbpath).session()
    player_repo = PlayerRepository(dbs)
    games_repo = GameRepository(dbs)
    players = [
        Player(name="jose"),
        Player(name="maria"),
        Player(name="carlos"),
        Player(name="ana"),
        Player(name="luis"),
        Player(name="sofia"),
    ]
    games = [
        Game(name="Partida 1", max_players=4, min_players=2, started=False),
        Game(name="Partida 2", max_players=3, min_players=2, started=False),
        Game(name="Partida 3", max_players=4, min_players=3, started=True),
        Game(name="Partida 4", max_players=2, min_players=2, started=False),
        Game(name="Partida 5", max_players=3, min_players=2, started=False),
    ]
    for player in players:
        logging.info("Guardando jugador %s", player.name)
        player_repo.save(player)

    logging.info("Agregando jugadores a partidas")
    games[0].add_player(players[0])  # jose a Partida 1
    games[0].add_player(players[1])  # maria a Partida 1
    games[1].add_player(players[2])  # carlos a Partida 2
    games[2].add_player(players[3])  # ana a Partida 3
    games[3].add_player(players[4])  # luis a Partida 4
    games[4].add_player(players[5])  # sofia a Partida 5
    for game in games:
        logging.info("Guardando partida %s", game.name)
        games_repo.save(game)
    logging.info("Data de testeo guardada exitosamente")


if __name__ == "__main__":
    main()
