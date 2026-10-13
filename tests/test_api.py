import pytest
from fastapi.testclient import TestClient

from api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_unknown_route_returns_404(client):
    response = client.get("/does_not_exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_create_task_rejects_blank_title(client):
    response = client.post("/tasks",
                           json={"title": ""}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1]=="title"