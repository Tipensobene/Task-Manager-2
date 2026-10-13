from getpass import getpass

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from orm_models import TaskRecord


password = getpass("Enter your password:\n")

database_url = URL.create(
    # 填写连接信息
    drivername='postgresql+psycopg',
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="task_manager_learning"
)

engine = create_engine(database_url)

with Session(engine) as session:
    task = session.get(TaskRecord, 2)

    if task is None:
        print("Task not found")
    else:
        print("修改前：", task.priority)

        # TODO：直接把task.priority修改为"high"
        task.priority="high"
        # TODO：flush，让UPDATE在当前事务中执行
        session.flush()
        print("flush后：", task.priority)

        # TODO：rollback，撤销UPDATE
        session.rollback()
        print("事务已回滚")