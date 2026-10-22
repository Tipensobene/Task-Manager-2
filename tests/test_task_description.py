"""备注功能的隔离回归：只使用内存数据库，不连接本机或容器PostgreSQL。"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api import app
from database import get_session
from orm_models import Base, TaskRecord
from task_service import TaskService


@pytest.fixture
def description_client():
    # StaticPool让接口使用的不同线程共享同一个内存数据库。
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


@pytest.mark.parametrize("fields, expected", [
    ({}, ""),
    ({"description": "  note  "}, "note"),
    ({"description": "   "}, ""),
    ({"description": "  " + "x" * 500 + "  "}, "x" * 500),
])
def test_create_detail_and_list_return_description(description_client, fields, expected):
    # 例如传入“  note  ”，创建响应、重新查询详情及列表都应得到“note”。
    response = description_client.post("/tasks", json={"title": "test", **fields})
    assert response.status_code == 201
    task = response.json()
    assert task["description"] == expected
    detail = description_client.get(f"/tasks/{task['id']}")
    assert detail.status_code == 200
    assert detail.json()["description"] == expected
    listing = description_client.get("/tasks")
    assert listing.status_code == 200
    assert listing.json()[0]["description"] == expected


@pytest.mark.parametrize("value", [None, 123, "x" * 501])
def test_create_rejects_invalid_description(description_client, value):
    response = description_client.post(
        "/tasks", json={"title": "test", "description": value},
    )
    assert response.status_code == 422
    assert description_client.get("/tasks").json() == []


@pytest.mark.parametrize("fields, expected", [
    ({}, "original"),
    ({"description": "  replacement  "}, "replacement"),
    ({"description": ""}, ""),
    ({"description": "   "}, ""),
    ({"description": "  " + "x" * 500 + "  "}, "x" * 500),
])
def test_patch_preserves_or_replaces_description(description_client, fields, expected):
    task = description_client.post(
        "/tasks", json={"title": "test", "description": "original"},
    ).json()
    url = f"/tasks/{task['id']}"
    response = description_client.patch(url, json=fields)
    assert response.status_code == 200
    assert response.json()["description"] == expected
    assert description_client.get(url).json()["description"] == expected


@pytest.mark.parametrize("value, status", [(None, 400), (123, 422), ("x" * 501, 422)])
def test_invalid_patch_keeps_existing_description(description_client, value, status):
    task = description_client.post(
        "/tasks", json={"title": "test", "description": "original"},
    ).json()
    url = f"/tasks/{task['id']}"
    assert description_client.patch(url, json={"description": value}).status_code == status
    assert description_client.get(url).json()["description"] == "original"


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("value", [None, 123, "x" * 501])
def test_service_rejects_invalid_description_without_saving(operation, value):
    # 直接调用Service，绕过Pydantic，防止接口校验掩盖Service的类型检查遗漏。
    repository = Mock()
    task = TaskRecord(title="test", description="original")
    repository.get_by_id.return_value = task
    service = TaskService(repository)
    with pytest.raises(ValueError):
        if operation == "create":
            service.create_task("test", description=value)
        else:
            service.update_task(1, {"description": value})
    assert task.description == "original"
    repository.add_task.assert_not_called()
    repository.get_tag_by_name.assert_not_called()
