from getpass import getpass

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

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

engine = create_engine(database_url)

with Session(engine) as session:
    # TODO：创建TaskRecord对象
    # title="ORM提交练习"
    # priority="high"

    new_task = TaskRecord(
        title="ORM提交练习",
        priority="high"
    )

    # TODO：加入Session
    session.add(new_task)
    print("commit前的ID：", new_task.id)

    # TODO：提交事务，不主动调用flush()
    session.commit()
    print("commit后的ID：", new_task.id)
    print("任务已提交")