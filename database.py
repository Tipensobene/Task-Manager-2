import os

from sqlalchemy import create_engine,URL
from sqlalchemy.orm import Session,sessionmaker
from collections.abc import Generator

# getenv() 在变量缺失时默认返回 None，错误可能拖到连接数据库时才出现。当前使用 os.environ[...] 可以更早发现配置缺失。
# 获取环境变量'TASK_MANAGER_DB_PASSWORD'的值
database_password=os.environ['TASK_MANAGER_DB_PASSWORD']

database_url=URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=database_password,
    host=os.getenv("TASK_MANAGER_DB_HOST","localhost"),
    port=5432,
    database=os.getenv(
        "TASK_MANAGER_DB_NAME",
        "task_manager_learning",
    ),
)

engine = create_engine(database_url)

SessionFactory = sessionmaker(bind=engine)

def get_session()->Generator[Session,None,None]:
    with SessionFactory() as session:
        yield session
