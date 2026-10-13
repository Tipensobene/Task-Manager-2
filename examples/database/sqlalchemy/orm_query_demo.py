from getpass import getpass

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

from orm_models import TaskRecord


password = getpass("Enter your password:\n")
task_id = int(input("Enter task id:\n"))

database_url = URL.create(
    # 由你填写数据库连接参数
    drivername='postgresql+psycopg',
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="task_manager_learning"
)

engine = create_engine(database_url)

with Session(engine) as session:
    # TODO：使用 session.get()，
    # 根据 task_id 查询 TaskRecord

    task=session.get(TaskRecord,task_id)

    # TODO：如果结果是 None，打印 Task not found
    if task is None:
        print("Task not found")

    # TODO：否则分别打印任务的四个属性
    else:
        print(task.id)
        print(task.title)
        print(task.done)
        print(task.priority)