import unittest 
from fastapi.testclient import TestClient
import asserts
from model import Game, Player
from main import app, player_repo, game_repo

client = TestClient(app)

def test_add_game():
    p = Player(name="Alice", identifier="0123456789abcdef0123456789abcdef")
    player_repo.save(p)
    games = [Game(name=f"game {n}") for n in range(10)]
    for game in games:
        game.set_defaults()
        game_repo.save(game)
    response = client.put("/api/lobby/1", json={"id_game":1, "identifier_player":"0123456789abcdef0123456789abcdef"})
    asserts.assert_equal(response.status_code, 200)

    
    

        
