from database import SessionFactory
from orm_models import TaskRecord

with SessionFactory() as session:

    task=session.get(TaskRecord,1)

    if task is None:
        print("Task not found")
    else:
        print(task.id)
        print(task.title)
        print(task.done)
        print(task.priority)
