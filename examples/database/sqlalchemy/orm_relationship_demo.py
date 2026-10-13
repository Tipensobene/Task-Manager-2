from getpass import getpass

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from orm_models import TaskRecord


password = getpass("Enter your password:\n")
task_id = int(input("Enter task id:\n"))

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

with Session(engine) as session:
    task = session.get(TaskRecord, task_id)

    if task is None:
        print("Task not found")
    else:
        print("任务：", task.title)
        print("标签：")

        # TODO：遍历task.tags
        # 分别打印每个tag.name
        for tag in task.tags:
            print(f"tag_name:{tag.name}")