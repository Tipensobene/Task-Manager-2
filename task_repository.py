

from sqlalchemy import select,func
from sqlalchemy.orm import Session, selectinload

from orm_models import TaskRecord,TagRecord


class TaskRepository:

    def __init__(self,session:Session):
        self.session=session

    def list_tasks(
            self,
            priority:str|None=None,
            done:bool|None=None,
            keyword:str|None=None,
            tag:str|None=None,
    )->list[TaskRecord]:

        statement=(
            select(TaskRecord)
        )

        if priority is not None:
            statement=statement.where(TaskRecord.priority==priority)

        if done is not None:
            statement=statement.where(TaskRecord.done==done)

        if keyword is not None:
            statement=statement.where(
                TaskRecord.title.ilike(f"%{keyword}%")
            )

        if tag is not None:
            statement=statement.where(
                TaskRecord.tags.any(TagRecord.name==tag)
            )

        statement=(statement
                   .options(
                        selectinload(TaskRecord.tags),
                   )
                   .order_by(TaskRecord.id.asc())
        )

        result=self.session.scalars(statement).all()
        result=list(result)

        return result

    def get_by_id(self,task_id:int)->TaskRecord|None:

        result=self.session.get(
            TaskRecord,
            task_id,
            options= [
                selectinload(TaskRecord.tags),
            ],
        )

        return result

    def add_task(self,task:TaskRecord)->TaskRecord:

        self.session.add(task)
        self.session.flush()

        return task

    def get_tag_by_name(self,name:str)->TagRecord|None:

        statement=(
            select(TagRecord)
            .where(TagRecord.name==name)
        )

        return self.session.scalar(statement)

    def get_stats(self)->dict[str,int]:
        statement=(
            select(
                func.count(TaskRecord.id)
                .label("total"),

                func.count(TaskRecord.id)
                .filter(TaskRecord.done.is_(False))
                .label("uncompleted_num"),

                func.count(TaskRecord.id)
                .filter(TaskRecord.done.is_(True))
                .label("completed_num"),
            )
        )

        row=self.session.execute(statement).mappings().one()

        return {
            "total":row["total"],
            "completed_num": row["completed_num"],
            "uncompleted_num":row["uncompleted_num"],

        }

    def delete_task(
        self,
        task:TaskRecord,
    )->None:
        self.session.delete(task)
        self.session.flush()
