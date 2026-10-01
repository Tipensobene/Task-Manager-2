from fastapi import FastAPI
from service import TaskManager
from storage import load_tasks
from fastapi import HTTPException
app = FastAPI(title="Task Manager3.0")

@app.get("/tasks")
def get_tasks():
    tasks = load_tasks()
    manager = TaskManager(tasks)

    task_list=manager.list_tasks()

    result=[]
    for task in task_list:
        result.append(task.to_dict())

    return result

@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    tasks = load_tasks()
    manager = TaskManager(tasks)


    target=manager.get_task(task_id)

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return target.to_dict()

