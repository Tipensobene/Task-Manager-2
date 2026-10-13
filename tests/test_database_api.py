import pytest


def test_create_and_get_database_task(database_client):
    response=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest事务隔离测试",
            "priority":"high",
            "tags":["pytest-isolation"],
        },
    )

    response_data=response.json()

    assert response.status_code == 201
    assert response_data["title"]=="pytest事务隔离测试"
    assert response_data["priority"]=="high"
    assert response_data["done"] is False
    assert response_data["tags"]==["pytest-isolation"]

    task_id=response_data["id"]

    detail_response=database_client.get(
        f"/database/tasks/{task_id}",
    )
    detail_data=detail_response.json()

    assert detail_response.status_code == 200
    assert detail_data==response_data

def test_create_completed_and_get_database_task(database_client):
    create_response=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest多次提交测试",
            "priority":"normal",
            "tags":["pytest-multi-commit"],
        },
    )

    assert create_response.status_code == 201

    created_task=create_response.json()
    task_id=created_task["id"]

    assert created_task["done"] is False

    complete_response=database_client.patch(
        f"/database/tasks/{task_id}/complete",
    )
    completed_task=complete_response.json()

    assert complete_response.status_code == 200
    assert completed_task["done"] is True
    assert completed_task["title"]=="pytest多次提交测试"
    assert completed_task["priority"]=="normal"
    assert completed_task["tags"]==["pytest-multi-commit"]

    detail_response=database_client.get(
        f"/database/tasks/{task_id}",
    )
    detail_task=detail_response.json()
    assert detail_response.status_code == 200
    assert detail_task==completed_task

def test_update_and_delete_database_task(database_client):
    create_response=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest更新删除测试",
            "priority":"low",
            "tags":["pytest-before-update"],
        }
    )

    assert create_response.status_code == 201
    task_id=create_response.json()["id"]

    update_response=database_client.patch(
        f"/database/tasks/{task_id}",
        json={
            "title":"pytest更新后任务",
            "priority":"high",
            "tags":["pytest-after-update"],
        }
    )

    assert update_response.status_code == 200
    updated_task=update_response.json()
    assert updated_task["done"] is False
    assert updated_task["priority"]=="high"
    assert updated_task["tags"]==["pytest-after-update"]
    assert updated_task["title"]=="pytest更新后任务"

    delete_response=database_client.delete(
        f"/database/tasks/{task_id}",

    )
    assert delete_response.status_code == 200
    assert delete_response.json()==updated_task

    get_response=database_client.get(
        f"/database/tasks/{task_id}",
    )
    assert get_response.status_code == 404
    assert get_response.json()=={"detail":"Task not found"}

@pytest.mark.parametrize(
    "invalid_priority",
    ["urgent","",None],
    ids=["unknown","empty","null"],
)
def test_create_rejects_invalid_priority(
        database_client,
        invalid_priority,
):
    response=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest非法优先级测试",
            "priority":invalid_priority,
        },
    )

    response_data=response.json()

    assert response.status_code == 422
    assert response_data["detail"][0]["loc"][-1]=="priority"
