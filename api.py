from fastapi import FastAPI
from service import TaskManager
from storage import load_tasks
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field
app = FastAPI(title="Task Manager3.0")

#响应模型
class TaskResponse(BaseModel):
    id:int
    title:str
    done:bool
    priority:str

@app.get("/tasks",response_model=list[TaskResponse])
def get_tasks(priority:str|None=None,done:bool|None=None):
    tasks = load_tasks()
    manager = TaskManager(tasks)

    if priority is None:
        task_list = manager.list_tasks()

    else:
        try:
            task_list = manager.search_by_priority(priority)

        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error)
            )


    result=[]

    if done is not None:
        filtered_tasks=[]

        for task in task_list:
            if task.done==done:
                filtered_tasks.append(task)

        task_list=filtered_tasks


    for task in task_list:
        result.append(task.to_dict())


    return result

@app.get("/tasks/{task_id}",response_model=TaskResponse)
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

class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title:str=Field(min_length=1,max_length=100)
    priority:str="normal"

@app.post("/tasks",status_code=201,response_model=TaskResponse)
def create_task(task: TaskCreate):


    tasks = load_tasks()
    manager = TaskManager(tasks)

    try:
        new_task=manager.add_task(task.title,task.priority)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)

        )

    return new_task.to_dict()

@app.patch("/tasks/{task_id}/complete",response_model=TaskResponse)
def complete_task(task_id: int):

    tasks = load_tasks()
    manager = TaskManager(tasks)

    if manager.get_task(task_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    try:
        completed_task = manager.complete_task(task_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return completed_task.to_dict()

@app.delete("/tasks/{task_id}",response_model=TaskResponse)
def delete_task(task_id: int):
    tasks = load_tasks()
    manager = TaskManager(tasks)

    try:
        deleted_task=manager.delete_task(task_id)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return deleted_task.to_dict()






