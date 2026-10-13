import pytest

def test_filter_by_priority_and_done(database_client):
    response_a=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest过滤任务A",
            "priority":"high",
        }
    )
    assert response_a.status_code == 201
    a_id=response_a.json()["id"]

    response_b=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest过滤任务B",
            "priority":"high",
        }
    )
    assert response_b.status_code == 201
    b_id=response_b.json()["id"]

    complete_response=database_client.patch(
        f"/database/tasks/{b_id}/complete",
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["done"] is True

    response_c=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest过滤任务C",
            "priority":"normal",
        }
    )
    assert response_c.status_code == 201
    c_id=response_c.json()["id"]

    response_list=database_client.get(
        "/database/tasks",
        params={
            "priority":"high",
            "done":False,
        }
    )

    assert response_list.status_code == 200

    tasks=response_list.json()
    for task in tasks:
        assert task["priority"] == "high"
        assert task["done"] is False

    returned_ids=[task["id"] for task in tasks]
    assert a_id in returned_ids
    assert b_id not in returned_ids
    assert c_id not in returned_ids

def test_filter_by_tag_preserves_all_tags(database_client):
    response_a=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest标签过滤A",
            "tags":["pytest-filter-python", "pytest-filter-database"],
        }
    )

    assert response_a.status_code == 201
    a_id=response_a.json()["id"]

    response_b=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest标签过滤B",
            "tags":["pytest-filter-java"],
        }
    )

    assert response_b.status_code == 201
    b_id=response_b.json()["id"]

    response_by_tag=database_client.get(
        "/database/tasks",
        params={
            "tag":"  PYTEST-FILTER-PYTHON  "
        }
    )

    assert response_by_tag.status_code == 200
    result_ids=[task["id"] for task in response_by_tag.json()]
    assert a_id in result_ids
    assert b_id not in result_ids

    assert result_ids.count(a_id) == 1

    for task in response_by_tag.json():
        if task["id"]==a_id:
            assert "pytest-filter-python" in task["tags"]
            assert "pytest-filter-database" in task["tags"]

@pytest.mark.parametrize(
    "query_name",
    ["keyword","tag"],
)
# 参数化会自动让测试函数执行n次
def test_filter_rejects_blank_query(database_client, query_name):
    response=database_client.get(
        "/database/tasks",
        params={query_name:"    "},
    )

    assert response.status_code == 400

    expected_details={
        "keyword":"Keyword cannot be empty",
        "tag":"Tag cannot be empty",
    }
    actual_detail=response.json()["detail"]
    expected_detail=expected_details[query_name]

    assert actual_detail == expected_detail
