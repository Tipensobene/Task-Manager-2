import pytest
from fastapi import Depends,FastAPI
from fastapi.testclient import TestClient

demo_app = FastAPI()

def get_message():
    return "production"

@demo_app.get("/message")
def read_message(message:str=Depends(get_message)):
    return {"message": message}

def override_get_message():
    return "test"

@pytest.fixture
def override_client():
    demo_app.dependency_overrides[get_message] = override_get_message

    yield TestClient(demo_app)

    demo_app.dependency_overrides.clear()

def test_dependency_override(override_client):
    response = override_client.get("/message")

    assert response.status_code ==200
    assert response.json() =={"message": "test"}
