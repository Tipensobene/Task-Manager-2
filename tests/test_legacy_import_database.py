import json

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from legacy_import import LegacyTaskInput, import_legacy_tasks, import_legacy_file
from orm_models import TaskRecord, TagRecord
from task_service import TaskService


@pytest.fixture
def import_file_session(database_session, monkeypatch):
    import database

    database_session.execute(delete(TaskRecord))
    factory = sessionmaker(
        bind=database_session.connection(),
        join_transaction_mode="create_savepoint",
    )
    monkeypatch.setattr(database, "SessionFactory", factory)
    return database_session


def test_import_rejects_target_with_existing_tasks(
        database_session
):
    database_session.add(TaskRecord(title="已有任务"))
    database_session.flush()
    source_tasks = [
        LegacyTaskInput.model_validate(
            {
                "id": 3, "title": "待导入任务"
            }
        )
    ]

    with pytest.raises(
            ValueError,
            match="Target database already contains tasks"
    ):
        import_legacy_tasks(database_session, source_tasks)


def test_import_preserves_tasks_and_reuses_tags(
        database_session
):
    # 仅在夹具事务内构造空任务表，结束后回滚恢复已有测试数据。
    database_session.execute(delete(TaskRecord))
    source_tasks = [
        LegacyTaskInput.model_validate(
            {
                "id": 3,
                "title": "已完成旧任务",
                "done": True,
                "priority": "high",
                "tags": ["pytest-legacy-shared"],
            }
        ),
        LegacyTaskInput.model_validate(
            {
                "id": 8,
                "title": "未完成旧任务",
                "tags": ["pytest-legacy-shared"],
            }
        ),
    ]

    mapping = import_legacy_tasks(database_session, source_tasks)
    database_session.expire_all()
    saved_tasks = database_session.scalars(
        select(TaskRecord).order_by(TaskRecord.id)
    ).all()

    assert set(mapping) == {3, 8}
    assert len(set(mapping.values())) == 2
    assert len(saved_tasks) == 2
    by_id = {task.id: task for task in saved_tasks}
    first = by_id[mapping[3]]
    second = by_id[mapping[8]]
    assert first.title == "已完成旧任务"
    assert first.done is True
    assert first.priority == "high"
    assert second.title == "未完成旧任务"
    assert second.done is False
    assert second.priority == "normal"
    assert first.created_at is not None
    assert second.created_at is not None
    assert [tag.name for tag in first.tags] == ["pytest-legacy-shared"]
    assert [tag.id for tag in first.tags] == [tag.id for tag in second.tags]
    shared_tags = database_session.scalars(
        select(TagRecord).where(TagRecord.name == "pytest-legacy-shared")
    ).all()
    assert len(shared_tags) == 1


def test_import_file_saves_batch_and_rejects_repeat(tmp_path, import_file_session):
    file_path = tmp_path / "tasks.json"
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump([
            {"id": 3, "title": "文件导入任务", "done": True},
            {"id": 8, "title": "文件导入第二条"},
        ], file)

    mapping = import_legacy_file(file_path)
    import_file_session.expire_all()
    saved_tasks = import_file_session.scalars(select(TaskRecord)).all()
    assert {task.id for task in saved_tasks} == set(mapping.values())
    assert len(saved_tasks) == 2
    assert import_file_session.get(TaskRecord, mapping[3]).done is True

    with pytest.raises(ValueError, match="Target database already contains tasks"):
        import_legacy_file(file_path)

    assert len(import_file_session.scalars(select(TaskRecord)).all()) == 2


def test_import_file_rolls_back_partial_batch(
        tmp_path,
        import_file_session,
        monkeypatch
):
    file_path = tmp_path / "tasks.json"
    tag_name = "pytest-legacy-batch-rollback"
    assert import_file_session.scalar(
        select(TagRecord).where(TagRecord.name == tag_name)
    ) is None
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump([
            {"id": 3, "title": "先写入的任务", "tags": [tag_name]},
            {"id": 8, "title": "触发模拟失败"},
        ], file)

    original_create = TaskService.create_task
    created_ids = []

    def fail_on_second(service, title, priority="normal", tags=None):
        if created_ids:
            # 证明第一条确已flush，而非在开始写入前失败。
            assert service.repository.session.get(TaskRecord, created_ids[0]) is not None
            raise RuntimeError("Simulated second task failure")
        task = original_create(service, title=title, priority=priority, tags=tags)
        created_ids.append(task.id)
        return task

    monkeypatch.setattr(TaskService, "create_task", fail_on_second)
    with pytest.raises(RuntimeError, match="Simulated second task failure"):
        import_legacy_file(file_path)

    import_file_session.expire_all()
    assert len(created_ids) == 1
    assert import_file_session.scalars(select(TaskRecord)).all() == []
    assert import_file_session.scalar(
        select(TagRecord).where(TagRecord.name == tag_name)
    ) is None
