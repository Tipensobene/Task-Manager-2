from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.orm import Session

from database import get_session
from task_repository import TaskRepository
from task_service import TaskService
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

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
    tags:list[str]|None=None

#响应模型
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str
    done:bool
    priority:str
    tags:list[str]

    @field_validator("tags",mode="before")
    @classmethod
    def convert_tags(cls,tags):

        return [
            tag if isinstance(tag,str) else tag.name
            for tag in tags
        ]



class TaskStatsResponse(BaseModel):
    total:int
    completed_num:int
    uncompleted_num:int


@task_router.get(
    "/stats",
    response_model=TaskStatsResponse
)
def get_task_stats(
        session:Session=Depends(get_session),
):
    repository=TaskRepository(session)
    service=TaskService(repository)

    return service.get_stats()

@task_router.get("",response_model=list[TaskResponse])
def get_tasks(
    priority:str|None=None,
    done:bool|None=None,
    keyword:str|None=None,
    tag:str|None=None,
    session:Session=Depends(get_session),
):

    repository=TaskRepository(session)
    service=TaskService(repository)

    try:
        return service.list_tasks(
            priority=priority,
            done=done,
            keyword=keyword,
            tag=tag,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@task_router.get("/{task_id}",response_model=TaskResponse)
def get_task(
        task_id: int,
        session:Session=Depends(get_session),
):

    repository=TaskRepository(session)
    service=TaskService(repository)


    target=service.get_task(task_id)

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return target



@task_router.post(
    "",
    status_code=201,
    response_model=TaskResponse
)
def create_task(
        task: TaskCreate,
        session:Session=Depends(get_session),
):

    repository=TaskRepository(session)
    service=TaskService(repository)


    try:
        new_task=service.create_task(
            task.title,
            task.priority,
            task.tags,
        )

        session.commit()
        session.refresh(new_task)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)

        )

    return new_task

@task_router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
)
def complete_task(
        task_id: int,
        session:Session=Depends(get_session),
):
    repository=TaskRepository(session)
    service=TaskService(repository)

    completed_task=service.complete_task(task_id)

    if completed_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    session.commit()
    session.refresh(completed_task)

    return completed_task


@task_router.delete(
    "/{task_id}",
    response_model=TaskResponse
)
def delete_task(
        task_id: int,
        session:Session=Depends(get_session),
):
    repository=TaskRepository(session)
    service=TaskService(repository)

    deleted_task=service.delete_task(task_id)

    if deleted_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    session.commit()

    return deleted_task

@task_router.patch(
    "/{task_id}",
    response_model=TaskResponse
)
def update_task(
        task_id: int,
        task_update: TaskUpdate,
        session:Session=Depends(get_session),
):
    repository=TaskRepository(session)
    service=TaskService(repository)

    update_data=task_update.model_dump(
        exclude_unset=True,
    )

    try:
        updated_task=service.update_task(
            task_id,
            update_data,
        )



    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if updated_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    session.commit()
    session.refresh(updated_task)
    return updated_task
