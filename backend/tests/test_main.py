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

