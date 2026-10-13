def test_task_stats_change_after_create_and_complete(database_client):
    baseline_response=database_client.get(
        "/database/tasks/stats",
    )

    assert baseline_response.status_code == 200

    baseline_stats=baseline_response.json()

    new_response=database_client.post(
        "/database/tasks",
        json={
            "title":"pytest基线测试",
            "priority":"normal",
        },
    )

    assert new_response.status_code == 201
    new_task_id=new_response.json()["id"]

    newline_response=database_client.get(
        "/database/tasks/stats",
    )


    assert newline_response.status_code == 200

    newline_stats=newline_response.json()
    assert newline_stats["total"]==baseline_stats["total"]+1
    assert newline_stats["completed_num"]==baseline_stats["completed_num"]
    assert newline_stats["uncompleted_num"]==baseline_stats["uncompleted_num"]+1

    completed_new_response=database_client.patch(
        f"/database/tasks/{new_task_id}/complete",
    )

    assert completed_new_response.status_code == 200

    third_response_stats=database_client.get(
        "/database/tasks/stats",
    )

    assert third_response_stats.status_code == 200

    thirdline_stats=third_response_stats.json()

    assert thirdline_stats["total"]==baseline_stats["total"]+1
    assert thirdline_stats["completed_num"]==baseline_stats["completed_num"]+1
    assert thirdline_stats["uncompleted_num"]==baseline_stats["uncompleted_num"]
