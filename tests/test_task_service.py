import pytest

from orm_models import TagRecord, TaskRecord
from task_repository import TaskRepository
from task_service import TaskService


def test_service_creates_task_with_normalized_tags(
        database_session,
):
    existing_tag = TagRecord(
        name="pytest-service-existing",
    )
    database_session.add(existing_tag)
    database_session.flush()

    repository = TaskRepository(database_session)
    service = TaskService(repository)

    task = service.create_task(
        "  pytest Service创建测试  ",
        "HIGH",
        [
            " Python ",
            "database",
            "PYTHON",
            " PYTEST-SERVICE-EXISTING ",
        ],
    )

    assert task.id is not None
    assert task.title == "pytest Service创建测试"
    assert task.priority == "high"
    assert task.done is False

    tag_names = [
        tag.name
        for tag in task.tags
    ]
    assert tag_names == [
        "python",
        "database",
        "pytest-service-existing",
    ]

    # is 检查是否为同一个Python对象，能更直接表达“Service复用了Session中已有的标签对象”，而不是只检查两个对象是否相等。
    saved_existing_tag=repository.get_tag_by_name(
        "pytest-service-existing"
    )
    assert saved_existing_tag is existing_tag

    default_task = service.create_task(
        "pytest Service默认测试"
    )

    assert default_task.priority == "normal"
    assert default_task.done is False
    assert default_task.tags == []


@pytest.mark.parametrize(
    ("title", "priority", "tags", "expected_message"),
    [
        ("   ", "normal", None, "Task title cannot be empty"),
        ("pytest非法优先级", "urgent", None, "Priority must be low, normal, or high"),
        ("pytest空标签", "normal", ["   "], "Tag cannot be empty"),
    ]
)
def test_service_rejects_invalid_input(
        database_session,
        title,
        priority,
        tags,
        expected_message,
):
    repository = TaskRepository(database_session)
    service = TaskService(repository)

    with pytest.raises(
            ValueError,
            match=expected_message,
    ):
        service.create_task(
            title,
            priority,
            tags,
        )

def test_service_list_tasks_with_normalized_filters(
        database_session,
):

    repository = TaskRepository(database_session)
    service = TaskService(repository)

    task_a = service.create_task(
        title="pytest Alpha Service",
        priority="high",
        tags=["pytest-service-filter-x"],
    )

    task_b = service.create_task(
        title="pytest Alpha Completed",
        priority="high",
        tags=["pytest-service-filter-x"],
    )
    task_b.done = True

    task_c = service.create_task(
        title="pytest Alpha Normal",
        priority="normal",
        tags=["pytest-service-filter-y"],
    )

    database_session.flush()

    tasks=service.list_tasks(
        priority="HIGH",
        done=False,
        keyword="ALPHA",
        tag=" PYTEST-SERVICE-FILTER-X ",
    )

    ids=[task.id for task in tasks]

    assert task_b.id not in ids
    assert task_a.id in ids
    assert task_c.id not in ids

@pytest.mark.parametrize(
    ("priority","keyword","tag","expected_message"),
    [
        ("urgent",None,None,"Priority must be low, normal, or high"),
        (None," ",None,"Keyword cannot be empty"),
        (None,None," ","Tag cannot be empty"),
    ]
)
def test_service_rejects_invalid_list_filters(
        database_session,
        priority,
        keyword,
        tag,
        expected_message,
        done=False,
):
    repository = TaskRepository(database_session)
    service = TaskService(repository)

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        service.list_tasks(
            priority,
            done,
            keyword,
            tag,
        )

def test_service_update_task(
        database_session,

):
    repository = TaskRepository(database_session)
    service = TaskService(repository)

    test_task = service.create_task(
        title="test_service_update_task",
        priority="normal",
        tags=["pytest-service-update-task"],
    )


    test_task_id=test_task.id

    test1_changed_task=service.update_task(
        test_task_id,
        update_data={
            "title": "test_service_update_task_changed",
        }
    )
    assert test1_changed_task.title == "test_service_update_task_changed"
    assert test1_changed_task.priority == "normal"
    assert ([
        tag.name
        for tag in test1_changed_task.tags
            ]
            == ["pytest-service-update-task"])

    test2_changed_task=service.update_task(
        test_task_id,
        update_data={
            "title": "  test_service_update_task_changed2     ",
            "priority": "high",
            "tags": ["  pytest-service-update-task    "],
        }
    )

    assert test2_changed_task.title == "test_service_update_task_changed2"
    assert test2_changed_task.priority == "high"
    assert ([
        tag.name
        for tag in test2_changed_task.tags
            ]
            == ["pytest-service-update-task"])

    test_illegal_task=service.update_task(
        -1,
        update_data={
            "title": "  test_service_update_task_changed3     ",
        }
    )

    assert test_illegal_task is None


    with pytest.raises(
        ValueError,
        match="title cannot be null",
    ):
        service.update_task(
        test_task_id,
        update_data={
            "title":None,
        },
        )

    with pytest.raises(
        ValueError,
        match="Priority must be low, normal, or high",
    ):
        service.update_task(
        test_task_id,
        update_data={
            "priority":"urgent",
        }
        )

    with pytest.raises(
        ValueError,
        match="Tag cannot be empty",
    ):

        service.update_task(
        test_task_id,
        update_data={
            "tags":["   "],
        }
        )

    test_clean_tags_task=service.update_task(
        test_task_id,
        update_data={
            "tags":[],
        }
    )

    assert test_clean_tags_task is not None
    assert test_clean_tags_task.tags==[]
