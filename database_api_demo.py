from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select,func
from pydantic import BaseModel,ConfigDict,field_validator,Field
from typing import Literal

from database import get_session
from orm_models import TaskRecord,TagRecord

Priority=Literal["low","normal","high"]
# 模型可以过滤不合法的输入形式

class DatabaseTaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title:str=Field(min_length=1,max_length=100)
    priority:Priority="normal"
    tags:list[str]=Field(default_factory=list)

class DatabaseTaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title:str|None=Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    priority:Priority|None=None
    tags:list[str]|None=None

class DatabaseTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:int
    title:str
    done:bool
    priority:str
    tags:list[str]

    @field_validator("tags", mode="before")
    @classmethod
    def convert_tags(cls,tags):
        return [tag.name for tag in tags]

class DatabaseTaskStatsResponse(BaseModel):
    total:int
    completed_num:int
    uncompleted_num:int

app = FastAPI(title="Database API Demo")




@app.get("/database/tasks",response_model=list[DatabaseTaskResponse],)
def get_database_tasks(
        priority:Priority|None=None,
        done:bool|None=None,
        keyword:str|None=None,
        tag:str|None=None,
        session: Session = Depends(get_session),
):
    statement = (
        select(TaskRecord)
        .options(
            selectinload(TaskRecord.tags)
        )
    )


    if priority is not None:
        statement=statement.where(TaskRecord.priority == priority)

    if done is not None:
        statement=statement.where(TaskRecord.done == done)

    if keyword is not None:

        keyword=keyword.lower().strip()

        if not keyword:
            raise HTTPException(
                status_code=400,
                detail="Keyword cannot be empty",
            )

        statement=statement.where(TaskRecord.title.ilike(f"%{keyword}%"))

    if tag is not None:
        cleaned_tag=tag.lower().strip()

        if not cleaned_tag:
            raise HTTPException(
                status_code=400,
                detail="Tag cannot be empty",
            )
        statement=statement.where(
            TaskRecord.tags.any(TagRecord.name == cleaned_tag)
        )

    statement=statement.order_by(TaskRecord.id.asc())

    tasks=session.scalars(statement).all()

    return tasks

@app.get("/database/tasks/stats",
         response_model=DatabaseTaskStatsResponse,
)
def get_database_task_stats(
        session: Session = Depends(get_session),
):
    statement = (
        select(
            func.count(TaskRecord.id)
            .label("total"),

            func.count(TaskRecord.id)
            .filter(TaskRecord.done.is_(True))
            .label("completed_num"),

            func.count(TaskRecord.id)
            .filter(TaskRecord.done.is_(False))
            .label("uncompleted_num"),
        )
    )

    row=session.execute(statement).mappings().one()

    return {
        "total":row["total"],
        "completed_num":row["completed_num"],
        "uncompleted_num":row["uncompleted_num"]
    }

@app.get("/database/tasks/{task_id}",response_model=DatabaseTaskResponse)
def get_database_task(
        task_id: int,
        session: Session = Depends(get_session),
):
    # TODO：使用session.get()查询TaskRecord
    task = session.get(
        TaskRecord,
        task_id,
        options=[
            selectinload(TaskRecord.tags)
        ]
    )
    # TODO：找不到时抛出404
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    # TODO：返回包含id、title、done、priority的字典
    return task
    # return {
    #     "id": task.id,
    #     "title": task.title,
    #     "done": task.done,
    #     "priority": task.priority,
    #     "tags": [tag.name for tag in task.tags],
    # }

@app.post(
    "/database/tasks",
    status_code=201,
    response_model=DatabaseTaskResponse,
)
def create_database_task(
        task_data:DatabaseTaskCreate,
        session:Session = Depends(get_session),
):
    # 清理客户端传来的非法格式和重复标签
    cleaned_tags=[]

    for tag in task_data.tags:
        clean_tag=tag.lower().strip()

        if not clean_tag:
            raise HTTPException(
                status_code=400,
                detail="Tag cannot be empty",
            )
        if clean_tag not in cleaned_tags:
            cleaned_tags.append(clean_tag)


    #创建ORM模型
    new_task=TaskRecord(
        title=task_data.title,
        priority=task_data.priority,
    )


    session.add(new_task)

    #筛选未出现的标签加入tag表 追加new_task_tags
    for tag_name in cleaned_tags:
        tag_record = session.scalar(
            select(TagRecord)
            .where(TagRecord.name == tag_name)
        )

        if tag_record is None:
            tag_record = TagRecord(name=tag_name)

        new_task.tags.append(tag_record)

    session.commit()
    session.refresh(new_task)

    return new_task

@app.patch(
    "/database/tasks/{task_id}",
    response_model=DatabaseTaskResponse,
)
def update_database_task(
        task_id:int,
        task_update:DatabaseTaskUpdate,
        session: Session = Depends(get_session),
):
    task=session.get(
        TaskRecord,
        task_id,
        options=[selectinload(TaskRecord.tags)],
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    update_data=task_update.model_dump(exclude_unset=True)

    # 拒绝客户端传递显式null
    for field_name,value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} cannot be null",
            )

    if "title" in update_data:
        task.title=update_data["title"]

    if "priority" in update_data:
        task.priority=update_data["priority"]

    if "tags" in update_data:
        cleaned_tags=[]

        for tag in update_data["tags"]:
            clean_tag=tag.lower().strip()

            if not clean_tag:
                raise HTTPException(
                    status_code=400,
                    detail="Tag cannot be empty",
                )
            if clean_tag not in cleaned_tags:
                cleaned_tags.append(clean_tag)

        task.tags.clear()

        for tag_name in cleaned_tags:
            tag_record = session.scalar(
                select(TagRecord)
                .where(TagRecord.name == tag_name)
            )

            if tag_record is None:
                tag_record=TagRecord(name=tag_name)

            task.tags.append(tag_record)

    session.commit()
    session.refresh(task)

    return task

@app.delete(
    "/database/tasks/{task_id}",
    response_model=DatabaseTaskResponse,
)
def delete_database_task(
        task_id:int,
        session: Session = Depends(get_session),
):
    task=session.get(
        TaskRecord,
        task_id,
        options=[selectinload(TaskRecord.tags)],
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    session.delete(task)
    session.commit()

    return task

@app.patch(
    "/database/tasks/{task_id}/complete",
    response_model=DatabaseTaskResponse,
)
def complete_database_task(
        task_id:int,
        session: Session = Depends(get_session),
):
    task=session.get(
        TaskRecord,
        task_id,
        options=[selectinload(TaskRecord.tags)],
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.done=True

    session.commit()
    session.refresh(task)

    return task
