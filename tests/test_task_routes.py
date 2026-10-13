import pytest

from orm_models import TaskRecord


def test_create_task_with_database(task_client):

    response=task_client.post(
        '/tasks',
        json={
        "title":" 正式接口pytest测试 ",
        "priority":"HIGH",
        "tags":[" Python ", "database", "PYTHON"],
        },
    )

    response_data=response.json()

    assert response.status_code == 201
    assert response_data["title"]=="正式接口pytest测试"
    assert response_data["priority"]=="high"
    assert response_data["done"] is False
    assert sorted(response_data["tags"])==["database","python"]

    task_id=response_data["id"]

    detail_response=task_client.get(
        f"/tasks/{task_id}",
    )

    detail_data=detail_response.json()

    assert detail_response.status_code == 200
    assert detail_data["id"]==task_id
    assert detail_data["title"]=="正式接口pytest测试"
    assert detail_data["priority"]=="high"
    assert detail_data["done"] is False
    assert sorted(detail_data["tags"])==["database","python"]

def test_get_missing_task_returns_404(task_client):
    response=task_client.get("/tasks/-1")

    assert response.status_code == 404
    assert response.json() == {"detail":"Task not found"}

def test_get_tasks_with_params(
        task_client,
        database_session,
):
    response_a=task_client.post(
        '/tasks',
        json={
            "title": "pytest Alpha Route",
            "priority": "HIGH",
            "tags": ["pytest-route-filter-x"],
        }
    )
    a_data=response_a.json()

    response_b=task_client.post(
        "/tasks",
        json={
            "title": "pytest Alpha Completed",
            "priority": "HIGH",
            "tags": ["pytest-route-filter-x"],
        }
    )
    b_data=response_b.json()

    response_c=task_client.post(
        "/tasks",
        json={
            "title": "pytest Alpha Normal",
            "priority": "normal",
            "tags": ["pytest-route-filter-y"],
        }
    )
    c_data=response_c.json()

    saved_b=database_session.get(
        TaskRecord,
        b_data["id"],
    )

    assert saved_b is not None

    saved_b.done=True
    database_session.flush()

    response=task_client.get(
        "/tasks",
        params={
            "priority": " HIGH ",
            "done": False,
            "keyword": " ALPHA ",
            "tag": " PYTEST-ROUTE-FILTER-X "
        },
    )

    assert response.status_code == 200

    response_data=response.json()
    response_ids=[task["id"] for task in response_data]
    assert a_data["id"] in response_ids
    assert b_data["id"] not in response_ids
    assert c_data["id"] not in response_ids

@pytest.mark.parametrize(
    ("params","expected_detail"),
    [
        (
            {"priority":"urgent"},
            "Priority must be low, normal, or high",
        ),
        (
            {"keyword":"    "},
            "Keyword cannot be empty",
        ),
        (
            {"tag":"    "},
            "Tag cannot be empty",
        ),
    ],
)
def test_get_tasks_rejects_invalid_filters(
        task_client,
        params,
        expected_detail,
):
    response=task_client.get(
        '/tasks',
        params=params,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail":expected_detail,
    }

def test_get_tasks_rejects_invalid_done(
        task_client,
):
    response=task_client.get(
        "/tasks",
        params={
            "done":"not-a-bool"
        }
    )
    assert response.status_code == 422

def test_get_stats(
        task_client,
        database_session,
):
    basic_response=task_client.get(
        "/tasks/stats",
    )
    assert basic_response.status_code == 200
    basic_data=basic_response.json()

    test_task=task_client.post(
        "/tasks",
        json={
            "title": "pytest_get_stats",
            "priority": "HIGH",
            "tags": ["pytest-stats-route"],
        }
    )
    assert test_task.status_code == 201
    test_data=test_task.json()

    middle_response=task_client.get(
        "/tasks/stats",
    )
    assert middle_response.status_code == 200
    middle_data=middle_response.json()

    assert middle_data["total"]==basic_data["total"]+1
    assert (middle_data["uncompleted_num"]
            ==basic_data["uncompleted_num"]+1
    )
    assert (middle_data["completed_num"]
            ==basic_data["completed_num"]
    )

    saved_task=database_session.get(
        TaskRecord,
        test_data["id"],
    )
    assert saved_task is not None

    saved_task.done=True
    database_session.flush()

    new_response=task_client.get(
        "/tasks/stats",
    )
    assert new_response.status_code == 200
    new_data=new_response.json()

    assert new_data["total"]==basic_data["total"]+1
    assert (new_data["uncompleted_num"]
            ==basic_data["uncompleted_num"])
    assert (new_data["completed_num"]
            ==basic_data["completed_num"]+1)

def test_completed_task(
        task_client,
):
    new_data=task_client.post(
        "/tasks",
        json={
            "title": "pytest_completed_task",
            "priority": "HIGH",
            "tags": ["pytest-completed-task"],
        }
    )

    assert new_data.status_code == 201
    new_task=new_data.json()
    assert new_task["done"] is False

    completed_data=task_client.patch(
        f"/tasks/{new_task["id"]}/complete",
    )

    assert completed_data.status_code == 200
    completed_task=completed_data.json()
    assert completed_task["done"] is True

    saved_data=task_client.get(
        f"/tasks/{new_task['id']}",
    )

    assert saved_data.status_code == 200
    saved_task=saved_data.json()
    assert saved_task["done"] is True

    illegal_data=task_client.patch(
        "/tasks/-1/complete"
    )

    assert illegal_data.status_code == 404
    assert illegal_data.json() == {
        "detail":"Task not found",
    }

def test_delete_task(
        task_client,
):
    new_data=task_client.post(
        "/tasks",
        json={
            "title": "pytest_delete_task",
            "priority": "HIGH",
            "tags": ["pytest-delete-task"],
        }
    )
    assert new_data.status_code == 201
    new_task=new_data.json()

    deleted_json=task_client.delete(
        f"/tasks/{new_task['id']}",
    )

    assert deleted_json.status_code == 200
    deleted_task=deleted_json.json()

    assert deleted_task["id"]==new_task["id"]
    assert deleted_task['title']==new_task['title']
    assert deleted_task["tags"]==new_task["tags"]

    no_data=task_client.get(
        f"/tasks/{new_task['id']}",
    )

    assert no_data.status_code == 404

    illegal_data=task_client.delete(
        "/tasks/-1",
    )

    assert illegal_data.status_code == 404
    assert illegal_data.json() == {
        "detail":"Task not found",
    }

def test_update_task(
        task_client,
):
    new_data=task_client.post(
        "/tasks",
        json={
            "title": "pytest_update_task",
            "priority": "HIGH",
            "tags": ["pytest-update-task"],
        }
    )

    assert new_data.status_code == 201
    new_task=new_data.json()

    updated_data=task_client.patch(
        f"/tasks/{new_task['id']}",
        json={
            "title": "pytest_update_task_changed",
        }
    )

    assert updated_data.status_code == 200
    updated_task=updated_data.json()
    assert updated_task["priority"]==new_task["priority"]
    assert updated_task["tags"]==new_task["tags"]


    second_updated_task=task_client.patch(
        f"/tasks/{new_task['id']}",
        json={
            "title": "  pytest_update_task_changed2   ",
            "priority": "   high   ",
            "tags":["Python","python","database"],
        }
    )
    assert second_updated_task.status_code == 200
    second_updated_task=second_updated_task.json()
    assert (second_updated_task["title"]
            =="pytest_update_task_changed2")
    assert (sorted(second_updated_task["tags"])
            == ["database", "python"])
    assert second_updated_task["priority"] == "high"

    final_data=task_client.get(
        f"/tasks/{new_task['id']}",
    )
    assert final_data.status_code == 200
    saved_task = final_data.json()

    assert saved_task["title"] == "pytest_update_task_changed2"
    assert saved_task["priority"] == "high"
    assert sorted(saved_task["tags"]) == ["database", "python"]

    illegal_data=task_client.patch(
        "/tasks/-1/",
        json={

        },
    )

    assert illegal_data.status_code == 404

@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        (
            {"title": None},
            "title cannot be null",
        ),
        (
            {"priority": "urgent"},
            "Priority must be low, normal, or high",
        ),
        (
            {"tags": ["   "]},
            "Tag cannot be empty",
        ),
    ],
)
def test_update_task_detail_by_param(
        payload,
        expected_detail,
        task_client,
):

    new_data=task_client.post(
        "/tasks",
        json={
            "title": "pytest_update_task",
            "priority": "HIGH",
            "tags": ["pytest-update-task"],
        }
    )

    assert new_data.status_code == 201
    new_task=new_data.json()

    response=task_client.patch(
        f"/tasks/{new_task['id']}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()=={
        "detail":expected_detail,
    }
