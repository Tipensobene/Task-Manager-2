from fastapi import FastAPI
from service import TaskManager
from storage import load_tasks

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