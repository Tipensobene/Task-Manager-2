from sqlalchemy import select
from getpass import getpass

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
from orm_models import TaskRecord

password = getpass("Enter your password:\n")

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

statement=(
    select(TaskRecord)
    .where(TaskRecord.done.is_(False))
    .order_by(TaskRecord.id.asc())
)

with Session(engine) as session:
    #scalars()返回select(xxx,yyyy)中所有第一个对象（xxx）
    # 直接提取查询结果中的ORM对象，不把它们再包在额外的行对象中。
    # (TaskRecord对象,)→TaskRecord对象
    result=session.scalars(statement)

    #tasks = result.all()取全部结果，返回一个序列，使用体验接近list[TaskRecord]
    tasks=result.all()


    for task in tasks:
        print(task.id,task.title,task.priority)