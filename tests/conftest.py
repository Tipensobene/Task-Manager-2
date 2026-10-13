import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import engine,get_session
from api import app as task_app
from database_api_demo import app as database_app

@pytest.fixture
def database_client(database_session):
    def override_get_session():
        yield database_session


    database_app.dependency_overrides[get_session] = override_get_session

    try:
        yield TestClient(database_app)

    finally:# 失败后也尽力尝试清理遗留
        database_app.dependency_overrides.clear()



@pytest.fixture
def database_session():
    connection=engine.connect()
    outer_transaction=connection.begin()
    session=Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()

@pytest.fixture
def task_client(database_session):
    def override_get_session():
        yield database_session

    task_app.dependency_overrides[get_session] = override_get_session

    try:
        yield TestClient(task_app)

    finally:
        task_app.dependency_overrides.clear()