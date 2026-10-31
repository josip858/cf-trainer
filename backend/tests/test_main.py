from fastapi.testclient import TestClient

import cf_client
from main import app
import pytest

client = TestClient(app)


def test_read_main() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


@pytest.mark.xfail
def test_xfail() -> None:
    assert 2 + 2 == 4


@pytest.mark.slow
async def test_get_picks() -> None:
    solved_list = await cf_client.get_solved_list("josip858")
    response = client.get("/api/picks", params={"handle": "josip858"})

    assert response.status_code == 200
    assert len(response.json()["picks"]) == 3
    assert all(pick["problem"]["id"] not in solved_list for pick in response.json()["picks"])


@pytest.mark.parametrize("handle", ["", " ", "1", "this_name_contains_more_than_24_chars"])
def test_get_picks_prevent_fetch_on_invalid_handle(monkeypatch, handle) -> None:
    def mock(handle) -> None:
        pytest.fail("Should not be called on invalid handle")

    monkeypatch.setattr(cf_client, "get_user_rating", mock)
    response = client.get("/api/picks", params={"handle": handle})
    assert response.status_code == 400
    assert response.json()["detail"]=="Handle should contain between 3 and 24 characters, inclusive"

def test_get_picks_404_on_user_not_found(monkeypatch) -> None:
    async def fake_get_user_rating(handle) -> None:
        raise cf_client.CFUserNotFound("User not found")
    monkeypatch.setattr(cf_client, "get_user_rating", fake_get_user_rating)
    response = client.get("/api/picks", params={"handle": "jiaofoimvowšmfr"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_picks_503(monkeypatch)-> None:
    def mock(handle) -> None:
        raise cf_client.CFError("Simulated external service bug")
    monkeypatch.setattr(cf_client, "get_user_rating", mock)
    response=client.get("/api/picks", params={"handle": "josip858"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Simulated external service bug"