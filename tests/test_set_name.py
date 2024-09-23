import requests
import pytest 
import asserts
from database import Database
from model import Player
db = Database() 
Session = db.get_session()

@pytest.fixture
def name_of_player():
    return {
        "name": "Alice", 
        "identifier": "01" 
    }

@pytest.mark.end2end_test
def test_set_name_endpoint(name_of_player):
    response = requests.post(f"http://0.0.0.0:8000/api/name", json={"name": "Alice"})
    player = Session.query(Player).filter_by(identifier="01").first()
    assert player is not None
    assert response.status_code == 201
    assert response.json() == name_of_player 

