from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_read_main()-> None:
    response =client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message":"Hello World!"}

@pytest.mark.xfail
def test_xfail()-> None:
    assert 2+2==4
