from getpass import getpass

from sqlalchemy import URL, create_engine, text


password = getpass("Enter your password:\n")
task_id = int(input("Enter task id:\n"))

database_url = URL.create(
    drivername='postgresql+psycopg',
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="task_manager_learning"
)

engine = create_engine(database_url)

statement = text(
    """
    SELECT
        id,
        title,
        done,
        priority
    FROM tasks
    WHERE id = :task_id;
    """
)

parameters={'task_id':task_id}

with engine.connect() as connection:
    # TODO：执行 statement，并传入名为 task_id 的参数字典
    result=connection.execute(
        statement,
        parameters
    )
    # TODO：取得一行
    row=result.mappings().fetchone()
    # TODO：判断是否为 None，然后打印
    if row is not None:
        print(row)
    else:
        print("No row found")