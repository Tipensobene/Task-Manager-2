from getpass import getpass

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import Session, selectinload

from orm_models import TaskRecord


password = getpass("Enter your password:\n")

database_url = URL.create(
    # 填写连接参数
    drivername='postgresql+psycopg',
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="task_manager_learning"
)

engine = create_engine(
    database_url,
    echo=True,
)

statement = (
    select(TaskRecord)
    .options(
        selectinload(TaskRecord.tags)
    )
    .order_by(TaskRecord.id.asc())
    # TODO：使用options和selectinload预加载TaskRecord.tags
    # TODO：按TaskRecord.id升序排列

)

with Session(engine) as session:
    # TODO：使用scalars执行查询并取得全部任务

    result=session.scalars(statement)
    tasks=result.all()

    for task in tasks:
        print("任务：", task.title)
        print("标签：")

        for tag in task.tags:
            print(tag.name)