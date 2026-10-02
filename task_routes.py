from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from service import TaskManager
from storage import load_tasks

#创建任务路由器
task_router=APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title:str=Field(min_length=1,max_length=100)
    priority:str="normal"
    tags:list[str]=Field(default_factory=list)

#局部更新模型
class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title:str|None=Field(
        default=None,
        min_length=1,
        max_length=100
    )
    priority:str|None=None

#响应模型
class TaskResponse(BaseModel):
    id:int
    title:str
    done:bool
    priority:str
    tags:list[str]


class TaskStatsResponse(BaseModel):
    total:int
    completed_num:int
    uncompleted_num:int


@task_router.get("/stats",response_model=TaskStatsResponse)
def get_task_stats():
    tasks = load_tasks()
    manager = TaskManager(tasks)

    return manager.get_statistics()

@task_router.get("",response_model=list[TaskResponse])
def get_tasks(priority:str|None=None,done:bool|None=None,keyword:str|None=None):
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

    match_ids = []
    if keyword is not None:

        try:
            keyword_list=manager.search_task(keyword)

            for task in keyword_list:
                match_ids.append(task.id)

            keyword_filtered_tasks=[]
            for task in task_list:
                if task.id in match_ids:
                    keyword_filtered_tasks.append(task)

            task_list=keyword_filtered_tasks

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

@task_router.get("/{task_id}",response_model=TaskResponse)
def get_task(task_id: int):

    tasks =load_tasks()
    manager = TaskManager(tasks)


    target=manager.get_task(task_id)

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return target.to_dict()



@task_router.post(
    "",
    status_code=201,
    response_model=TaskResponse
)
def create_task(task: TaskCreate):


    tasks = load_tasks()
    manager = TaskManager(tasks)

    try:
        new_task=manager.add_task(task.title,task.priority,task.tags)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)

        )

    return new_task.to_dict()

@task_router.patch("/{task_id}/complete",response_model=TaskResponse)
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

@task_router.delete("/{task_id}",response_model=TaskResponse)
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

@task_router.patch("/{task_id}",response_model=TaskResponse)
def update_task(task_id: int,task_update: TaskUpdate):
    tasks = load_tasks()
    manager = TaskManager(tasks)

    task=manager.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=404
        )

    update_data=task_update.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} cannot be null"
            )

    try:
        res_data=manager.update_task(task_id,**update_data)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return res_data.to_dict()

