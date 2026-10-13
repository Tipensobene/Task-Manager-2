import pytest

from models import Task

@pytest.fixture
def sample_task():
    return Task(
        id=1,
        title="学习 pytest",
        priority="high",
        tags=["python"],
    )

def test_tasks_have_independent_tag_lists():
    task_a=Task(id=1,title="任务A")
    task_b=Task(id=2,title="任务B")

    task_a.tags.append("python")

    assert task_a.tags==["python"]
    assert task_b.tags==[]

def test_sample_task_title(sample_task):
    assert sample_task.title == "学习 pytest"

def test_sample_task_priority(sample_task):
    assert sample_task.priority == "high"

def test_sample_task_tags(sample_task):
    assert sample_task.tags == ["python"]

def test_sample_task_can_be_modified(sample_task):
    sample_task.tags.append("pytest")

    assert sample_task.tags == ["python","pytest"]

def test_sample_task_starts_with_original_tags(sample_task):
    assert sample_task.tags==["python"]
