from orm_models import TaskRecord,TagRecord
from task_repository import TaskRepository

def test_repository_lists_and_gets_tasks(database_session):

    tag=TagRecord(
        name="pytest-repository-read",

    )

    task=TaskRecord(
        title="pytest Repository查询测试",
        priority="high",
        tags=[tag],
    )

    database_session.add(task)
    database_session.flush()

    repository=TaskRepository(database_session)

    tasks=repository.list_tasks()

    task_ids=[saved_task.id for saved_task in tasks]

    assert task_ids==sorted(task_ids)
    assert task.id in task_ids

    saved_task=repository.get_by_id(task_id=task.id)

    assert saved_task is not None
    assert saved_task.title == "pytest Repository查询测试"
    assert saved_task.priority == "high"

    tag_names=[
        saved_tag.name
        for saved_tag in saved_task.tags
    ]
    assert "pytest-repository-read" in tag_names

    missing_task=repository.get_by_id(-1)
    assert missing_task is None

def test_repository_adds_task(database_session):

    repository=TaskRepository(database_session)

    task=TaskRecord(
        title="pytest Repository创建测试",
        priority="normal",
    )

    saved_task=repository.add_task(task)

    assert saved_task is task
    assert saved_task.id is not None
    assert saved_task.title=="pytest Repository创建测试"
    assert saved_task.priority=="normal"
    assert saved_task.done is False

    queried_task=repository.get_by_id(saved_task.id)
    assert queried_task is not None
    assert queried_task.id==saved_task.id
    assert queried_task.title==saved_task.title

def test_repository_gets_tag_by_name(database_session):

    tag=TagRecord(
        name="pytest-repository-tag",

    )

    database_session.add(tag)
    database_session.flush()

    repository=TaskRepository(database_session)
    saved_tag=repository.get_tag_by_name("pytest-repository-tag")

    assert saved_tag is not None
    assert saved_tag.id ==tag.id
    assert saved_tag.name==tag.name

    missing_tag=repository.get_tag_by_name(
        "pytest-repository-missing",
    )
    assert missing_tag is None

def test_repository_list_tasks(database_session):
    tag_x = TagRecord(
        name="pytest-repository-filter-x",
    )

    tag_y = TagRecord(
        name="pytest-repository-filter-y",
    )

    task_a=TaskRecord(
        title="pytest Alpha Repository",
        priority="high",
        done=False,
        tags=[tag_x],
    )


    task_b=TaskRecord(
        title="pytest Beta Repository",
        priority="high",
        done=True,
        tags=[tag_y],
    )


    task_c=TaskRecord(
        title="pytest Alpha Other",
        priority="normal",
        done=False,
        tags=[tag_y],
    )


    database_session.add(task_a)
    database_session.add(task_b)
    database_session.add(task_c)
    database_session.flush()
    a_id=task_a.id
    b_id=task_b.id
    c_id=task_c.id

    repository=TaskRepository(database_session)

    tasks_first=repository.list_tasks(
        priority="high",
        done=False,
    )

    ids_first=[saved_task.id for saved_task in tasks_first]
    assert a_id in ids_first
    assert b_id not in ids_first
    assert c_id not in ids_first

    tasks_second=repository.list_tasks(
        done=False,
    )

    ids_second=[saved_task.id for saved_task in tasks_second]
    assert a_id in ids_second
    assert b_id not in ids_second
    assert c_id in ids_second

    tasks_third=repository.list_tasks(
        keyword="alpha",
    )

    ids_third=[saved_task.id for saved_task in tasks_third]
    assert a_id in ids_third
    assert c_id in ids_third
    assert b_id not in ids_third

    tasks_fourth=repository.list_tasks(
        tag="pytest-repository-filter-x",
    )

    ids_fourth=[saved_task.id for saved_task in tasks_fourth]
    assert a_id in ids_fourth
    assert b_id not in ids_fourth
    assert c_id not in ids_fourth

    tasks_fifth=repository.list_tasks(
        keyword="alpha",
        tag="pytest-repository-filter-y",
    )

    ids_fifth=[saved_task.id for saved_task in tasks_fifth]
    assert a_id not in ids_fifth
    assert b_id not in ids_fifth
    assert c_id in ids_fifth

def test_repository_get_stats(database_session):

    repository=TaskRepository(database_session)

    basicline_stats=repository.get_stats()

    task_a = TaskRecord(
        title="pytest get stats uncompleted",
        priority="high",
        done=False,
        tags=[
            TagRecord(
                name="pytest-repository-uncompleted",
            )
        ],
    )

    database_session.add(task_a)

    task_b = TaskRecord(
        title="pytest get stats completed",
        priority="normal",
        done=True,
        tags=[
            TagRecord(
                name="pytest-repository-completed",
            )
        ]
    )

    database_session.add(task_b)

    database_session.flush()

    newline_stats=repository.get_stats()

    assert newline_stats["total"]==basicline_stats["total"]+2
    assert (newline_stats["uncompleted_num"]
            ==basicline_stats["uncompleted_num"]+1)
    assert (newline_stats["completed_num"]
            ==basicline_stats["completed_num"]+1)

def test_delete_task(
        database_session,
):
    new_tag=TagRecord(
        name="pytest-repository-delete-test",
    )
    database_session.add(new_tag)
    database_session.flush()

    new_task=TaskRecord(
        title="pytest-repository-delete-test",
        priority="normal",
        done=False,
        tags=[new_tag],
    )

    database_session.add(new_task)
    database_session.flush()

    new_id=new_task.id
    new_tag_name=new_tag.name

    repository=TaskRepository(database_session)
    repository.delete_task(new_task)

    deleted_task=repository.get_by_id(new_id)
    assert deleted_task is None

    remaining_tag=repository.get_tag_by_name(new_tag_name)
    assert remaining_tag is not None
