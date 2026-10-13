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
    # TODO：创建 TaskRecord对象
    # title 使用 "ORM事务练习"
    # priority 使用 "normal"
    new_task = TaskRecord(
        title="ORM事务练习",
        priority="normal"
    )

    print("flush前的ID：", new_task.id)

    # TODO：将对象加入Session
    session.add(new_task)
    # TODO：执行flush
    # 手动flush()主要用于：
    # - 提交前需要拿到自动生成的ID；
    # - 提交前需要让数据库检查约束；
    # - 一个事务中后续操作依赖前一步写入结果。
    session.flush()
    print("flush后的ID：", new_task.id)
    print("flush后的done：", new_task.done)

    # TODO：回滚事务
    session.rollback()
    print("事务已回滚")